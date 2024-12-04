# app that generates an assisstant for the user that needs buy https://platform.openai.com/docs/assistants/quickstart

import openai
from os import getenv
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler
import json
load_dotenv()

class EventHandler(AssistantEventHandler):    
    """
    EventHandler class that handles various events related to text creation, text delta, tool calls, and actions required by the assistant.
    Methods:
        on_text_created(text: str) -> None:
            Handles the event when text is created by the assistant. Prints the assistant prompt.
        on_text_delta(delta, snapshot) -> None:
            Handles the event when there is a change in the text. Prints the delta value.
        on_event(event) -> None:
            Handles general events. Specifically processes events that require action by the assistant.
        on_tool_call_created(tool_call) -> None:
            Handles the event when a tool call is created. Prints the type of tool call.
        on_tool_call_delta(delta, snapshot) -> None:
            Handles the event when there is a change in the tool call. Specifically processes code interpreter inputs and outputs.
        handle_requires_action(data, run_id) -> None:
            Processes actions required by the assistant. Retrieves product information or stock based on the tool calls and prepares the outputs.
        submit_tool_outputs(tool_outputs, run_id) -> None:
            Submits the tool outputs using the submit_tool_outputs_stream helper.
    """
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
      
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
    
    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)
      
    def on_tool_call_created(self, tool_call):
        #print(f"\nassistant > {tool_call.type}\n", flush=True)
        print(f"\nassistant > i'm searching...", end="", flush=False)
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
             
    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        
        for tool in data.required_action.submit_tool_outputs.tool_calls:           
            arguments = json.loads(tool.function.arguments)  # Convertir a diccionario
            if tool.function.name == "get_product_info":
                product_name = arguments["Name"].lower()
                product_info = next((item for item in catalog if item["Name"].lower() == product_name), None)
                if product_info:
                    tool_outputs.append({"tool_call_id": tool.id, "output": f"The product is {product_info['Name']} with description: {product_info['Description']} and price: {product_info['Price']}."})
                else:
                    tool_outputs.append({"tool_call_id": tool.id, "output": "Product not found."})
            elif tool.function.name == "get_product_stock":
                product_name = arguments["Name"].lower()
                product_stock = next((item for item in catalog if item["Name"].lower() == product_name), None)
                if product_stock:
                    tool_outputs.append({"tool_call_id": tool.id, "output": f"The product {product_stock['Name']} is in stock with availability: {product_stock['Stock_availabiility']}."})
                else:
                    tool_outputs.append({"tool_call_id": tool.id, "output": "Product not found."})
        
            elif tool.function.name == "get_all_products":
                products = [product["Name"] for product in catalog]
                tool_outputs.append({"tool_call_id": tool.id, "output": f"The available products are: {', '.join(products)}."})
                
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)
 
    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            for _ in stream.text_deltas:
                print(end="", flush=True)
            # print()



key= getenv("OPENAI_API_KEY")
# carga del json con los productos

with open("catalog.json") as file:
    catalog = json.load(file)
    
    
    


client = openai.Client()
thread = client.beta.threads.create()
assistant = client.beta.assistants.create(
    name="Shopping Assistant",
    description="Helps users find the right product to buy",
    model="gpt-4o",
    instructions="Help the user find the right product to buy",
    metadata={
        "category": "e-commerce"
    },
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_product_info",
                "description": "Get product information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Name": {
                            "description": "The name of the product",
                            "type": "string"
                        },
                    },
                    "required": ["Name"],
                    "additionalProperties": False
                },
                
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_stock",
                "description": "Get product stock",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Name": {
                            "description": "The name of the product",
                            "type": "string"
                        },
                    },
                    "required": ["Name"],
                    "additionalProperties": False
                },
               
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_products",
                "description": "Get all products",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Name": {
                            "description": "The name of the product",
                            "type": "string"
                        },
                    },
                    "required": ["Name"],
                    "additionalProperties": False
                },
            }
        }
    ]
)


with client.beta.threads.runs.stream(
    thread_id= thread.id,
    assistant_id=assistant.id,
    instructions="Help the user find the right product to buy",
    event_handler=EventHandler(),
) as stream:
  stream.until_done()


while True:
    user_input = input("\nuser > ")
    if user_input.strip().upper() == "END":
        print("Chat is finished.")
        break
    response =client.beta.threads.messages.create(thread.id, role="user", content=user_input)
    with client.beta.threads.runs.stream(
        thread_id= thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
        additional_instructions="You should help the user find the right product to buy and provide the information requested, you couldnt talk for another topics .",
    ) as stream:
        stream.until_done()
