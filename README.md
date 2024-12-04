# Shopping Assistant

This project is a Shopping Assistant application that helps users find the right product to buy. It uses OpenAI's API to interact with users and provide product information, stock availability, and a list of all available products.

## Features

- Retrieve product information including name, description, and price.
- Check stock availability for a specific product.
- List all available products.

## Requirements

The project requires the following Python packages:

- annotated-types==0.7.0
- anyio==4.6.2.post1
- certifi==2024.8.30
- colorama==0.4.6
- distro==1.9.0
- h11==0.14.0
- httpcore==1.0.7
- httpx==0.28.0
- idna==3.10
- jiter==0.8.0
- openai==1.56.1
- pyasn1==0.6.1
- pydantic==2.10.3
- pydantic_core==2.27.1
- python-dotenv==1.0.1
- rsa==4.9
- sniffio==1.3.1
- tqdm==4.67.1
- typing_extensions==4.12.2

## Installation

1. Clone the repository:

   ```sh
   git clone git@github.com:juandiegou/assistance.git 
   cd assistance
   ```

2. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your OpenAI API key:

   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Ensure you have a `catalog.json` file in the root directory with the product information.

## Usage

Run the application:

```sh
python [app.py] app.py
```
