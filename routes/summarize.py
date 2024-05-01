import numpy as np
from fastapi import FastAPI,Body,HTTPException,status,APIRouter,Depends

from dependencies.dependency import check_api_key

from openai import OpenAI
from config.settings import Settings
from models.models import Completion,SummarizeParams
import tiktoken


setting=Settings()

client = OpenAI(api_key=setting.OPENAI_API_KEY)

app = FastAPI()



async def calculate_tokens(text: str) -> int:
    
    if not text:
        return 0
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-instruct")
    tokens = encoding.encode(text)
    
    return len(tokens)


async def chunk_text(text: str,typ:str=None, lmx:int=None)->list:
    
    number_of_tokens = await calculate_tokens(text) #Calculate text tokens 
    estimated_tokens = await estimate_tokens(lmx,typ) #Estimate completion tokens
   
    words = text.split(" ")
    estim_prompt_tokens = 4097-estimated_tokens
    if estim_prompt_tokens >0:
        chunks = np.array_split(words, (number_of_tokens // (estim_prompt_tokens)) + 1)
        
        return chunks
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Completion is too long for this text. Please reduce the size of lmax")
       

async def create_completion(params: Completion,text:str ) -> str:
    
    response = client.completions.create(
        model=params.model,
        temperature=params.temperature,
        max_tokens=params.max_tokens,
        prompt=params.prompt + text
    )
    
    return response.choices[0].text

async def estimate_tokens(lmax: int,input_type:str) -> int:
    if input_type =="character":
        return lmax//4
    elif input_type =="word":
        return int(lmax * 1.3)
    return 0



async def valid_input_type(input_type:str):
    return input_type in ("character", "word","char")
        
        
        
router = APIRouter(prefix="/summarize")
@router.post('/')
async def get_final_summary(modell:SummarizeParams=Body(...),apikey:str=Depends(check_api_key)): 
    if modell.lmax <=0:
        raise HTTPException   (status_code=status.HTTP_400_BAD_REQUEST,detail="You requested a length 0 completion. Please request a completion with length at least 1.")
    
        
    if await valid_input_type(modell.typ) :  
        chunked_text =await chunk_text(modell.text,modell.typ,modell.lmax)
        number_of_chunks = len(chunked_text)
        

        summaries = ""
        for chunk in chunked_text:
            max_t = await estimate_tokens(modell.lmax,modell.typ)//number_of_chunks
            print("estimated comp tokens",max_t)
            
            
            completion_params = Completion(max_tokens=max_t)
            text_of_chunk = "".join(chunk)
            requested_tokens = await calculate_tokens(text_of_chunk) + max_t
            if requested_tokens > 4097:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"This model's maximum context length is 4097 tokens, however you requested {requested_tokens} tokens .Please reduce your prompt; or desired completion length.")
            else:
                summary = await create_completion(completion_params, text_of_chunk)
                summaries += summary 
        if modell.typ == "character" :

            return {"summary": summaries,"size":len(list(summaries))}
        else :
            
            return {"summary": summaries,"size":len((summaries.split(' ')))}
    else :
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="input must be 'character' or 'word'")



