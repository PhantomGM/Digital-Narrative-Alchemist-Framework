import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from layer5_dna_substrate.phenotype_meta import TAIL_INSTRUCTION

# Sanity bounds on a decoded page. The largest legitimate phenotype observed
# across five Session 0 trials is about 14 KB, so these are loose by design --
# they exist to catch degeneration, not to police length.
MAX_PHENOTYPE_CHARS = 100_000
MAX_TRAILING_PAD = 2_000


def format_context(context) -> str:
    """
    Normalizes a decode context into prompt-ready markdown.
    Accepts a ContextPackage (anything with for_decoder()), a string, or a
    legacy dict of notes.
    """
    if context is None:
        return "No additional context provided."
    if isinstance(context, str):
        return context or "No additional context provided."
    if hasattr(context, "for_decoder"):
        return context.for_decoder()
    if isinstance(context, dict):
        if not context:
            return "No additional context provided."
        return "\n".join(f"{key}: {value}" for key, value in context.items())
    return str(context)


class DNADecoder:
    """
    Translates raw DNA strings into rich, evocative TTRPG content using the Master Decoder prompts.
    """
    def __init__(self):
        from layer1_core.model_router import model_router
        self.llm = model_router.get_llm("dna_decoder", temperature=0.7)
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
                    
                    # Append the structured-tail requirement and the variable injection points
                    full_template = base_template + "\n\n" + TAIL_INSTRUCTION + "\n\nHere is the context provided (if any):\n{context}\n\n{constraints}\n\nHere is the DNA string to decode:\n{dna_string}\n\nPlease provide the final decoded profile:"
                    
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

    def decode_element(self, element_data: dict, context=None) -> str:
        """
        Master dispatcher for DNA decoding.

        context may be a ContextPackage (preferred), a pre-formatted string,
        or a legacy dict of notes.
        """
        element_type = element_data['type'].lower()
        if element_type in self.prompts:
            chain = self.prompts[element_type] | self.llm | self.parser
            context_str = format_context(context)
            constraints_str = element_data.get('constraints', '')
            
            phenotype = chain.invoke({
                "context": context_str,
                "dna_string": element_data['dna'],
                "constraints": constraints_str
            })

            # An empty response is never a valid decode, and silence is the
            # worst way for it to fail. In the trial 5 run a `culture` decode
            # came back blank after 39 seconds; the harness registered it,
            # wrote a zero-byte page, used it as context for everything
            # generated afterwards, and still reported the contract satisfied.
            # A world was short one of its contracted entities and nothing
            # anywhere said so. Raising is strictly better than returning "":
            # the caller can retry, and a caller that does not is at least
            # loud about it.
            if not (phenotype or "").strip():
                raise ValueError(
                    f"Decoding {element_type} returned an empty phenotype. "
                    f"The model produced nothing -- refused, filtered, or cut "
                    f"off. Retry or inspect the prompt; do not register this.")

            # Degenerate repetition. A 9/9 NPC decode produced a profile
            # truncated after the BDI block followed by roughly 1.8 MB of
            # trailing spaces -- the Gamemaster's Toolkit, the hooks and the
            # machine-readable tail all lost to padding. It passed the emptiness
            # check above, because 3 KB of real content plus a megabyte of
            # whitespace is not empty. The registry would have stored it, the
            # vault sync written it, and the missing half never mentioned.
            #
            # Two shapes, because the length cap alone misses the subtler one:
            # a profile of ordinary size wearing 50 KB of padding.
            padding = len(phenotype) - len(phenotype.rstrip())
            if padding > MAX_TRAILING_PAD:
                raise ValueError(
                    f"Decoding {element_type} returned {padding:,} characters of "
                    f"trailing whitespace -- the model degenerated into padding "
                    f"and the profile is almost certainly truncated. Retry.")
            if len(phenotype) > MAX_PHENOTYPE_CHARS:
                raise ValueError(
                    f"Decoding {element_type} returned {len(phenotype):,} "
                    f"characters. No profile is that long; this is runaway "
                    f"repetition. Retry or inspect the prompt.")
            return phenotype
        else:
            raise NotImplementedError(f"Decoding for {element_type} is not yet implemented or mapped. Check decoders directory.")
