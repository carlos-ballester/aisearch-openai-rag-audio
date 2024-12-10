import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from ragtools import attach_rag_tools
from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    #rtmt.system_message = "You are a helpful assistant. Only answer questions based on information you searched in the knowledge base, accessible with the 'search' tool. " + \
                          #"The user is listening to answers with audio, so it's *super* important that answers are as short as possible, a single sentence if at all possible. " + \
                          #"Never read file names or source names or keys out loud. " + \
                          #"Always use the following step-by-step instructions to respond: \n" + \
                          #"1. Always use the 'search' tool to check the knowledge base before answering a question. \n" + \
                          #"2. Always use the 'report_grounding' tool to report the source of information from the knowledge base. \n" + \
                          #"3. Produce an answer that's as short as possible. If the answer isn't in the knowledge base, say you don't know."

    rtmt.system_message = "You are a helpful and knowledgeable assistant. Let the user talk before speaking yourself and follow the instructions given by the user as long as they do not conflict with the instructions here. You can both answers questions based on your own knowledge of the world, which is vast and very complete, and also based on information you searched in the knowledge base, accessible with the 'search' tool, if there is relevant information there. " + \
                          "You can listen to full conversations, involving several people, and give insights once the full conversation has finished. To do this, you just simply need to listen to the realtime audio that is coming from the user microphone. Users might chose to label or announce their names before starting to talk, and you can also use that information to provide insights tied to an individual person." + \
                          "The user is listening to answers with audio, so it's *super* important that answers are on the short side rather than super long, a few sentences maximum. If the user interrupts you with the word stop, or someting similar in meaning, stop your answer and ask 'How can I help you next?' " + \
                          "Never read file names or source names or keys out loud. " + \
                          "Always use the following step-by-step instructions to respond: \n" + \
                          "1. Always use the 'search' tool to check the knowledge base before answering a question or giving insights about a conversation. \n" + \
                          "2. If you find results in the knowledge base, use the 'report_grounding' tool to report the source of information from the knowledge base. \n" + \
                          "3. Produce an answer that's complete and is based on the knowledge base, if you have found a result there, or in your vast existing knowledge if not, including providing an assessment of the full audio content that was given to you in form of question or audio input. "

    attach_rag_tools(rtmt,
        credentials=search_credential,
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or "default",
        identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
        content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
        embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
        title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
        use_vector_query=(os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY") == "true") or True
        )

    rtmt.attach_to_app(app, "/realtime")

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
