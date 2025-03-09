import json
import pytest
import logging
from unittest.mock import patch, MagicMock
from app import EventHandler

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar catálogo para pruebas
@pytest.fixture
def catalog():
    with open("catalog.json") as file:
        return json.load(file)

# Test: Carga del catálogo
def test_catalog_loading(catalog):
    assert isinstance(catalog, list), "El catálogo no se cargó correctamente"
    assert all(k in catalog[0] for k in ["Name", "Description", "Price", "Stock_availabiility"]), "Faltan campos en el JSON"
    logger.info("Prueba test_catalog_loading: PASADA")

# Crear clases para simular el acceso de atributos en lugar de un diccionario
class SubmitToolOutputs:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls

class RequiredAction:
    def __init__(self, submit_tool_outputs):
        self.submit_tool_outputs = submit_tool_outputs

class Data:
    def __init__(self, tool_calls):
        self.required_action = RequiredAction(SubmitToolOutputs(tool_calls))

# Función auxiliar para pruebas de herramientas
def run_tool_test(event_handler, tool_name, tool_args, expected_output, mock_submit_tool_outputs, run_id):
    tool_call = MagicMock()
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(tool_args)
    tool_call.id = run_id

    data = Data([tool_call])
    event_handler.handle_requires_action(data, run_id)

    mock_submit_tool_outputs.assert_any_call(
        [{"tool_call_id": tool_call.id, "output": expected_output}],
        run_id
    )

# Test: Verificar que las funciones de herramientas devuelven los resultados esperados
@pytest.mark.parametrize("tool_name, tool_args, expected_output, run_id", [
    ("get_all_products", {"Name": ""}, "The available products are: Apple MacBook Pro, Samsung Galaxy S21, Sony WH-1000XM4, Dell XPS 13, Apple iPhone 13, Bose QuietComfort 35 II, Microsoft Surface Pro 7, Google Pixel 6, Amazon Echo Dot (4th Gen), Fitbit Charge 5, HP Spectre x360, OnePlus 9 Pro, JBL Flip 5, Canon EOS R5, Nintendo Switch, Sony PlayStation 5, Samsung QLED TV, Dyson V11 Vacuum, GoPro HERO9, Apple AirPods Pro.", "test_tool_all_products"),
    ("get_product_info", {"Name": "Apple MacBook Pro"}, "The product is Apple MacBook Pro with description: 16-inch, 16GB RAM, 1TB SSD and price: 2399.", "test_tool_product_info"),
    ("get_product_info", {"Name": "TabletXYZ"}, "Product not found.", "test_tool_product_info_nonexistent"),
    ("get_product_stock", {"Name": "Apple MacBook Pro"}, "The product Apple MacBook Pro is in stock with availability: 15.", "test_tool_product_stock"),
    ("get_product_stock", {"Name": "TabletXYZ"}, "Product not found.", "test_tool_product_stock_nonexistent"),
])
@patch.object(EventHandler, 'submit_tool_outputs')
def test_tool_functions(mock_submit_tool_outputs, tool_name, tool_args, expected_output, run_id, catalog):
    event_handler = EventHandler()
    run_tool_test(event_handler, tool_name, tool_args, expected_output, mock_submit_tool_outputs, run_id)
    logger.info(f"Prueba {run_id}: PASADA")

# Test: Simular un flujo completo de interacción con el asistente
@patch.object(EventHandler, 'submit_tool_outputs')
def test_complete_interaction_flow(mock_submit_tool_outputs, catalog):
    event_handler = EventHandler()

    tool_calls = [
        ("get_product_info", {"Name": "Apple MacBook Pro"}, "The product is Apple MacBook Pro with description: 16-inch, 16GB RAM, 1TB SSD and price: 2399."),
        ("get_product_stock", {"Name": "Apple MacBook Pro"}, "The product Apple MacBook Pro is in stock with availability: 15."),
        ("get_product_info", {"Name": "Samsung Galaxy S21"}, "The product is Samsung Galaxy S21 with description: 128GB, Phantom Gray and price: 799."),
        ("get_product_stock", {"Name": "Samsung Galaxy S21"}, "The product Samsung Galaxy S21 is in stock with availability: 30."),
        ("get_product_info", {"Name": "Sony PlayStation 5"}, "The product is Sony PlayStation 5 with description: 825GB SSD, 4K Gaming Console and price: 499."),
        ("get_product_stock", {"Name": "Sony PlayStation 5"}, "The product Sony PlayStation 5 is currently out of stock."),
        ("get_product_info", {"Name": "Apple AirPods Pro"}, "The product is Apple AirPods Pro with description: Active Noise Cancellation, Wireless Charging and price: 249."),
        ("get_product_stock", {"Name": "Apple AirPods Pro"}, "The product Apple AirPods Pro is in stock with availability: 50."),
        ("END", {}, "Interaction ended.")
    ]
    run_id_prefix = "test_run_id_"

    for i, (tool_name, tool_args, expected_output) in enumerate(tool_calls):
        tool_call = MagicMock()
        tool_call.function.name = tool_name
        tool_call.function.arguments = json.dumps(tool_args)
        tool_call.id = f"{run_id_prefix}{i}"

        data = Data([tool_call])
        event_handler.handle_requires_action(data, f"{run_id_prefix}{i}")

    logger.info("Prueba test_complete_interaction_flow: PASADA")


# Test: Manejo de errores y casos límite
@patch.object(EventHandler, 'submit_tool_outputs')
def test_error_handling_and_edge_cases(mock_submit_tool_outputs, catalog):
    event_handler = EventHandler()

    tool_calls = [
        ("get_product_info", {"Name": ""}, "Product not found."),
        ("get_product_info", {"Name": "Laptop; DROP TABLES;"}, "Product not found."),
        ("get_product_info", {"Name": "<script>alert('hack')</script>"}, "Product not found."),
        ("get_product_info", {"Name": "   "}, "Product not found."),
        ("get_product_info", {"Name": "商品"}, "Product not found."),
        ("get_product_info", {"Name": "A" * 1000}, "Product not found."),
        ("get_product_info", {"Name": "@@@###$$$"}, "Product not found."),
        ("get_product_info", {"Name": "Laptop123!@#"}, "Product not found."),
    ]
    run_id_prefix = "test_run_id_error_"

    for i, (tool_name, tool_args, expected_output) in enumerate(tool_calls):
        run_tool_test(event_handler, tool_name, tool_args, expected_output, mock_submit_tool_outputs, f"{run_id_prefix}{i}")

    logger.info("Prueba test_error_handling_and_edge_cases: PASADA")
