import datetime
import re
from pymongo import MongoClient

# Clase de programa para generar archivo
def generate_report():
    # Entradas del usuario
    quarter_number = input("Introduce la quincena (1 o 2): ")
    quarterInput = f"{quarter_number}qday"
    billField = f"{quarter_number}qbill"
    
    # Conexion a BD de MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['unapec']

    # Conexion a tabla employees
    empls_collection = db['employees']
    unapec_empls = list(empls_collection.find({'employee': True}))

    # Conexion a tabla institution
    inst_collection = db['institution']
    inst_data = inst_collection.find_one({'college': "unapec"})

    # Conteo de archivos a procesar
    count = empls_collection.count_documents({'employee': True})

    # Manejo de excepciones si la tabla esta vacia
    try:
        doc_num = unapec_empls[0]['doc_num']
    except IndexError:
        print('No hay empleados para pagar nómina.')
        return

    # Crearcion de archivo generado
    filename = "nomina.txt"
    with open(filename, 'w') as f:

        # Header
        today = datetime.datetime.now().strftime("%Y%m%d")
        rnc = inst_data['rnc'].ljust(10)
        quarter_day = inst_data[quarterInput]
        quarter_date = datetime.datetime.now().replace(day=int(quarter_day)).strftime('%Y%m%d')
        apap_acc = inst_data['apap_acc'].ljust(12)

        # Calculo de total
        total_amount = sum([emp[billField] for emp in unapec_empls])
        total_amount_str = "{:.2f}".format(total_amount).rjust(14)

        header = f"N{rnc}{today}{quarter_date}{apap_acc}{total_amount_str}"
        f.write(header + "\n")

        # Body
        body = ''
        for employee in unapec_empls:
            doc_num = employee['doc_num'].ljust(11)
            doc_type = employee['doc_type']
            q1bill = "{:.2f}".format(employee['1qbill']).ljust(12)
            acc_num = employee['acc_num'].ljust(14)
            row = f"{doc_num}{doc_type}{q1bill}{acc_num}"
            body += row + "\n"
        f.write(body)

        # Footer
        count = str(count).zfill(9)
        footer = f"S{count}"
        f.write(footer)

    print("Archivo generado de forma satisfactoria.")

# Clase de programa para importar archivo
def process_input_file():
    filepath = input("Introduce la ruta del archivo: ").strip()

    # Regex para validar el layout
    header_pattern = re.compile(r'^N.{10}\d{8}\d{8}.{12}.{14}')
    body_pattern = re.compile(r'^.{11}.{1}.{12}.{14}')
    footer_pattern = re.compile(r'^S\d{9}')

    # Conexion a BD de MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['unapec']
    input_payments = db['input_payments']

    date = None

    try:
        with open(filepath, 'r') as file:
            for line in file:
                
                if header_pattern.match(line):
                    # Conversacion de fecha
                    date_str = line[19:26].strip()
                    date = datetime.datetime.strptime(date_str, "%Y%m%d")
                    
                elif body_pattern.match(line):
                    # Extraccion de datos en variables
                    doc_num = line[0:11].strip()
                    doc_type = line[11:12]
                    bill = float(line[12:24])
                    acc_num = line[25:40].strip()
                    
                    # Insert
                    input_payments.insert_one({'doc_num': doc_num, 'doc_type': doc_type, 'bill': bill, 'acc_num': acc_num, 'date': date})

                elif footer_pattern.match(line):
                    pass
                    print("Archivo procesado correctamente.")
                else:
                    raise ValueError("Layout no válido, por favor revisa el archivo.")
    except Exception as e:
        print(f"Error procesando el archivo: {str(e)}")

# Menu
def show_menu():
    while True:
        print("\nEscoge una opción:")
        print("1. Exportar archivo de nómina.")
        print("2. Importar archivo de nómina.")
        print("3. Salir")

        user_choice = input("Opción elegida: ")
        if user_choice == '1':
            generate_report()
        elif user_choice == '2':
            process_input_file()
        elif user_choice == '3':
            print("Saliendo del programa.")
            break
        else:
            print("Opción inválida, por favor digita una opción del menú.")

# Mostrar menu cuando corre el programa
show_menu()