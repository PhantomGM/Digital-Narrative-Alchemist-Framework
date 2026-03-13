import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class DNADecoder:
    """
    Translates raw DNA strings into rich, evocative TTRPG content using the Master Decoder prompts.
    """
    def __init__(self, llm_model="qwen3.5:397b-cloud"):
        api_key = os.getenv("OLLAMA_API_KEY", "dummy_key")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        
        self.llm = ChatOpenAI(
            model=llm_model, 
            temperature=0.7,
            api_key=api_key,
            base_url=base_url
        )
        self.parser = StrOutputParser()
        self.prompts = {}
        
        # Load all available decoder prompts from the decoders directory
        decoders_dir = os.path.join(os.path.dirname(__file__), 'decoders')
        if os.path.exists(decoders_dir):
            for filename in os.listdir(decoders_dir):
                if filename.endswith(".md"):
                    type_name = filename[:-3].lower()
                    with open(os.path.join(decoders_dir, filename), 'r', encoding='utf-8') as f:
                        base_template = f.read()
                    
                    # Append the necessary variable injection points
                    full_template = base_template + "\n\nHere is the context provided (if any):\n{context}\n\n{constraints}\n\nHere is the DNA string to decode:\n{dna_string}\n\nPlease provide the final decoded profile:"
                    
                    # Some prompts have curly braces like TRAVEL{4-2-2} or JSON examples in them,
                    # Langchain will try to parse them. To prevent crash, we use partial string formatting,
                    # or change template_format to f-string/jinja2. Better yet, escape native braces.
                    # A quick fix is to replace single braces with double braces, then revert our target variables.
                    sanitized_template = full_template.replace('{', '{{').replace('}', '}}')
                    sanitized_template = sanitized_template.replace('{{context}}', '{context}').replace('{{dna_string}}', '{dna_string}').replace('{{constraints}}', '{constraints}')
                    
                    self.prompts[type_name] = PromptTemplate(
                        template=sanitized_template,
                        input_variables=["context", "dna_string", "constraints"]
                    )

    def decode_element(self, element_data: dict, context: dict = None) -> str:
        """Master dispatcher for DNA decoding."""
        element_type = element_data['type'].lower()
        if element_type in self.prompts:
            chain = self.prompts[element_type] | self.llm | self.parser
            context_str = str(context) if context else "No additional context provided."
            constraints_str = element_data.get('constraints', '')
            
            return chain.invoke({
                "context": context_str,
                "dna_string": element_data['dna'],
                "constraints": constraints_str
            })
        else:
            raise NotImplementedError(f"Decoding for {element_type} is not yet implemented or mapped. Check decoders directory.")
