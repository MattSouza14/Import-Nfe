import pandas as pd
import re
import json

from bs4 import BeautifulSoup
from thefuzz import fuzz
from tkinter import Tk  
from tkinter.filedialog import askopenfilename
from colorama import Fore, Back, Style, init

Tk().withdraw()

def parse_tag_to_string(bs4_tag):
    remove_tag_regex = r'<\w+>(.*?)</\w+>'
    data = re.search(remove_tag_regex, str(bs4_tag))
    return data.group(1)

def parse_object_name(object_name):
    object_name = str(object_name).strip().lstrip('0')
    parsed_object_name = re.sub(r'\s{2,}', ' ', object_name)
    return parsed_object_name

def teste(name1, name2):
    if name1.startswith('PAO'):
        print(name1, len(name1))
        print(name2, len(name2))
        print(fuzz.partial_ratio(name1, name2) > 50)

def teste2(name, df_unity, product_unity):
    if name.startswith('PAO COCO'):
        print(name, df_unity, product_unity)

def get_product(codAlternativo, product_unity, product_name, ramifs):
    parsed_cod = parse_object_name(codAlternativo)
    parsed_name = parse_object_name(product_name)
    ramifs = ramifs.split(' ')

    cod_matches_filter = df['Alternativo'].apply(lambda cod: parse_object_name(cod) == parsed_cod)
    unity_matches_filter = df['Unidade'].apply(lambda df_unity: df_unity == product_unity)
    name_matches_filter = df['Descricao'].apply(lambda df_name: fuzz.partial_ratio(df_name, parsed_name) > 50 )
    cod_mae_matches_filter = df['Mae'].apply(lambda cod_mae: parse_object_name(cod_mae) in [parse_object_name(ramif) for ramif in ramifs])

    product = df.loc[unity_matches_filter  & name_matches_filter & cod_mae_matches_filter]
    return product

def parse_number(number):
    number = float(number)
    if int(number) - number != 0:
        return number
    else:
        return int(number)    

def trim_timezone_from_date(date_str):
    return date_str[:-6]

map_cnpj_to_org_and_user = { 
    "02974336000180": {"org": 2, "userId": 334, "userName": "Carlos_Eduardo"}, #Malibru Matriz
    "02974336000342": {"org": 18, "userId": 334, "userName": "Carlos_Eduardo"}, #Malibru Dist
    "02974336000504": {"org": 21, "userId": 334, "userName": "Carlos_Eduardo"}, #Malibru Santos Dumont
    "05635589000118": {"org": 16, "userId": 269, "userName": "Debora"}, #Dicoco Ceará
    "05635589000207": {"org": 17, "userId": 269, "userName": "Debora"}, #Dicoco Petrolândia
    "05635589000380": {"org": 20, "userId": 269, "userName": "Debora"}, #Dicoco Itapipoca
    "23487846000101": {"org": 23, "userId": 334, "userName": "Carlos_Eduardo"}, #Atacarejo Matriz
    "23487846000284": {"org": 25, "userId": 334, "userName": "Carlos_Eduardo"}, #Atacarejo Itarema
    "23487846000365": {"org": 26, "userId": 334, "userName": "Carlos_Eduardo"}, #Atacarejo Camocim
    "23487846000446": {"org": 29, "userId": 334, "userName": "Carlos_Eduardo"}, #Atacarejo Itapipoca
}

map_series_to_id = {
    "0":"95",
    "1":"71",
    "2":"99",
    "3":"98",
    "4":"105",
    "5":"106",
    "6":"113",
    "7":"112",
    "8":"115",
    "9":"137",
    "10":"141",
    "11":"159",
    "12":"218",
    "13":"220",
    "14":"207",
    "16":"158",
    "20":"138",
    "25":"190",
    "23":"236",
    "29":"233",
    "30":"213",
    "40":"119",
    "47":"157",
    "55":"110",
    "56":"238",
    "60":"170",
    "80":"165",
    "87":"116",
    "099":"225",
    "000":"121",
    "100":"118",
    "105":"216",
    "107":"189",
    "110":"203",
    "111":"184",
    "186":"172",
    "200":"139",
    "300":"162",
    "400":"206",
    "500":"163",
    "700":"205",
    "889":"108",
    "890":"164",
    "900":"96",
    "901":"101",
    "920":"202",
}

map_unidade = {
    "BAMBONA":{"id": 68, "nome": "Bambona"},
    "ARR":{"id": 1, "nome": "Unidade"},
    "BD":{"id": 64, "nome": "Balde"},
    "BB":{"id": 64, "nome": "Balde"},
    "Bl":{"id": 64, "nome": "Balde"},
    "BL":{"id": 66, "nome": "Bloco"},
    "BT":{"id": 1105, "nome": "Blister"},
    "BO":{"id": 67, "nome": "Bobina"},
    "BR":{"id": 1099, "nome": "Barra"},
    "CAIXA":{"id": 37, "nome": "Caixa"},
    "CX":{"id": 37, "nome": "Caixa"},
    "CART":{"id": 1089, "nome": "Cartela"},
    "CT":{"id": 65, "nome": "Cento"},
    "cto":{"id": 65, "nome": "Cento"},
    "DC":{"id": 1079, "nome": "Direcionador de Custo"},
    "DS":{"id": 1100, "nome": "DOSE"},
    "FARDO":{"id": 39, "nome": "Fardo"},
    "FD":{"id": 39, "nome": "Fardo"},
    "fdo":{"id": 39, "nome": "Fardo"},
    "FL":{"id": 1103, "nome": "Fileira"},
    "FR":{"id": 1080, "nome": "Frasco"},
    "FC":{"id": 1080, "nome": "Frasco"},
    "GL":{"id": 63, "nome": "Galão"},
    "gal":{"id": 63, "nome": "Galão"},
    "GR":{"id": 9, "nome": "Grama"},
    "GRF":{"id": 26, "nome": "Garrafa"},
    "H":{"id": 1088, "nome": "Hora"},
    "JG":{"id": 1097, "nome": "Jogo"},
    "KTS":{"id": 1098, "nome": "Kit"},
    "KIT":{"id": 1098, "nome": "Kit"},
    "KG":{"id": 2, "nome": "Quilograma"},
    "Kg":{"id": 2, "nome": "Quilograma"},
    "Km":{"id": 58, "nome": "Quilômetro"},
    "KW":{"id": 7, "nome": "Quilowatt hora"},
    "LITRO":{"id": 3, "nome": "Litro"},
    "LTO":{"id": 1094, "nome": "Litro"},
    "LT":{"id": 1094, "nome": "Litro"},
    "L":{"id": 1094, "nome": "Litro"},
    "LTA":{"id": 1101, "nome": "Lata"},
    "M2":{"id": 5, "nome": "Metro quadrado"},
    "MET":{"id": 5, "nome": "Metro quadrado"},
    "M3":{"id": 6, "nome": "Metro cúbico"},
    "MIL":{"id": 13, "nome": "Milheiro"},
    "MT":{"id": 4, "nome": "Metro linear"},
    "M":{"id": 4, "nome": "Metro linear"},
    "PCS":{"id": 1086, "nome": "Peça"},
    "PEC":{"id": 1086, "nome": "Peça"},
    "PCA":{"id": 1086, "nome": "Peça"},
    "PC":{"id": 1086, "nome": "Peça"},
    "Pc":{"id": 1086, "nome": "Peça"},
    "PCT":{"id": 34, "nome": "Pacote"},
    "pct":{"id": 34, "nome": "Pacote"},
    "PCT":{"id": 34, "nome": "Pacote"},
    "PT":{"id": 34, "nome": "Pacote"},
    "PL":{"id": 1091, "nome": "Paletes"},
    "PR":{"id": 71, "nome": "Par"},
    "PAR":{"id": 71, "nome": "Par"},
    "QT":{"id": 72, "nome": "Quarto"},
    "RL":{"id": 40, "nome": "Rolo"},
    "ROL":{"id": 40, "nome": "Rolo"},
    "RS":{"id": 69, "nome": "Resma"},
    "SC":{"id": 1093, "nome": "Saco"},
    "TAMBOR":{"id": 18, "nome": "Tambor"},
    "TB":{"id": 70, "nome": "Tubo"},
    "TON":{"id": 28, "nome": "Tonelada"},
    "TO":{"id": 28, "nome": "Tonelada"},
    "Ton":{"id": 28, "nome": "Tonelada"},
    "UN":{"id": 1, "nome": "Unidade"},
    "AM1":{"id": 1, "nome": "Unidade"},
    "Un":{"id": 1, "nome": "Unidade"},
    "und":{"id": 1, "nome": "Unidade"},
    "Um":{"id": 1, "nome": "Unidade"},
    "UND":{"id": 1, "nome": "Unidade"},
    "UNI":{"id": 1, "nome": "Unidade"},
    "un":{"id": 1, "nome": "Unidade"},
    "VR":{"id": 1102, "nome": "Volumes"},
    "VL":{"id": 59, "nome": "Volumes"},
    "CAR":{"id": 1095, "nome": "Carrada"},
    "KT":{"id": 1098, "nome": "KIT"}
}

columns = ["Alternativo","Objeto", "Descricao","CNPJ","CdFrn","NomeFrn", "Unidade", "Mae"]
df = pd.read_excel('prod.xlsx', header=None, names=columns, skiprows=list(range(4)))
df["Descricao"] = df["Descricao"].apply(lambda x: x.split(" - Cód.")[0])

# show an "Open" dialog box and return the path to the selected file(s)
filenames = askopenfilename(title="Escolher Notas", multiple=True) 

jsonList = []

for filename in filenames:
    print("*******************************************************************")
    print(f"Gerando nota de chave: {filename.split('/')[-1].split('.')[0]}")
    ramifs = input("Digite o(s) código(s) da(s) ramificação(ões) dos objetos dessa nota.\nSepare os códigos digitados por um espaço em branco: ")


    with open(filename, 'r') as f:
        data = f.read()

    xml_data = BeautifulSoup(data, "xml")
    products = xml_data.find_all(['xProd','NCM','uCom','qCom','vUnCom','vProd', 'cProd'])

    chaveNFe = xml_data.find(['chNFe'])
    chaveNFe = parse_tag_to_string(chaveNFe)

    dest_cnpj = xml_data.find('dest').find('CNPJ')
    dest_cnpj = parse_tag_to_string(dest_cnpj)

    numeroNota = xml_data.find('nNF')
    numeroNota = parse_tag_to_string(numeroNota)

    series = xml_data.find('serie')
    series = parse_tag_to_string(series)

    map_setor = {
        "Power EPI": [{"id":1,"nome":"Estoque"}, {"id":6,"nome":"Almoxarifado"}, { "id":79,"nome":"Etq. Recebimento"}],
        "Imobilizado": [{"id":6,"nome":"Imobilizado"}, {"id":3,"nome":"Administração"}, {"id":37,"nome":"Atv. Administrativa"}],
        #"Outros": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":3,"nome":"Administração"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Veiculos": [{"id":6,"nome":"Imobilizado"}, {"id":168,"nome":"Veiculos"}, {"id":4875,"nome":"Cadastro de Veiculos"}],
        "Trade e Marketing - 93767": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":164,"nome":"Trade e Marketing"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Terrenos": [{"id":6,"nome":"Imobilizado"}, {"id":145,"nome":"Terrenos"}, {"id":52912,"nome":"Fazendas"}],
        "Sistema de Plantacao de Coco Anao": [{"id":6,"nome":"Imobilizado"}, {"id":169,"nome":"Plantação"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Sistema de Perfuracao de Pocos": [{"id":6,"nome":"Imobilizado"}, {"id":157,"nome":"Perfuração de Poços"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Sistema de Irrigação": [{"id":6,"nome":"Imobilizado"}, {"id":154,"nome":"Irrigação"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Sistema de Energia Solar": [{"id":6,"nome":"Imobilizado"}, {"id":155,"nome":"Energia Solar"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Sistema de Desmatamento e Preparacao das Terras": [{"id":6,"nome":"Imobilizado"}, {"id":153,"nome":"Supressão"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Moveis e Utensilios": [{"id":6,"nome":"Imobilizado"}, {"id":150,"nome":"Móveis e Utensilios"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material para Manutenção da Instalação de Irrigação": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":116,"nome":"Irrigação"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material Manutenção de Estradas": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":141,"nome":"Estradas"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material Fazenda ( Demais Produtos )": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":122,"nome":"Material Agricola"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Uso Laboratorio": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":123,"nome":"Laboratório"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Segurança do Trabalho - EPI e Demais": [{"id":1,"nome":"Estoque"}, {"id":92,"nome":"EPIS"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Material de Monitoramento e Segurança": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":128,"nome":"Informática"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Manutenção de Máquinas/ Maquinário Industrial":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":134,"nome":"Máquinas e Equipamentos"}, {"id":60,"nome":"Atividade Industrial (Div)"}],
        "Material de Manutenção de Máquinas/ Maquinário Industrial":[{"id":1,"nome":"Estoque"}, {"id":134,"nome":"Máquinas e Equipamentos"}, {"id":60,"nome":"Atividade Industrial (Div)"}],
        "Material de Manutenção de Máquinas em Geral":[{"id":1,"nome":"Estoque"}, {"id":124,"nome":"Manutenção Predial"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Informática e Suprimentos":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":128,"nome":"Informática"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Higiene e Limpeza":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":125,"nome":"Limpeza"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Escritório":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":126,"nome":"Escritório"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Copa e Cozinha":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":139,"nome":"Copa"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Conservação Predial":[{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":124,"nome":"Manutenção Predial"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Acondicionamento, Conservação e Armazenagem - Materiais - 45296": [{"id":1,"nome":"Estoque"}, {"id":37,"nome":"Estoque de Embalagens"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Materiais de Embalagens": [{"id":1,"nome":"Estoque"}, {"id":37,"nome":"Estoque de Embalagens"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Máquinas e Equipamentos 2262": [{"id":6,"nome":"Imobilizado"}, {"id":147,"nome":"Maquinário Industrial"}, {"id":60,"nome":"Atividade Industrial (Div)"}],
        "Manutenção Veículos de Frota": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":18,"nome":"Logistica"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Manutenção de Maquinários Agrícolas": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":120,"nome":"Maquinário Agrícola"}, {"id":99645,"nome":"Placas - Linha Amarela"}],
        "Insumos Pecuários": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":123,"nome":"Pecuária"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Insumos para Cultivo e Formação do Solo": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":115,"nome":"Insumos Agrícolas"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Insumos": [{"id":1,"nome":"Estoque"}, {"id":42,"nome":"Estoque Matéria Prima"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Festas/Eventos e Confraternizações": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":127,"nome":"Eventos"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Ferramentas e Acessórios": [{"id":6,"nome":"Imobilizado"}, {"id":149,"nome":"Ferramentas"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Feiras, Eventos e Agências": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":163,"nome":"Feiras, Eventos e Agências"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Farmácia": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":144,"nome":"Primeiros Socorros"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Fardamentos": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":118,"nome":"Fardamento"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Equip de Proteção Individual ( EPI ) - c/ Pis e Cofins": [{"id":1,"nome":"Estoque"}, {"id":92,"nome":"EPIS"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Energia": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":3,"nome":"Administração"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Edificações": [{"id":6,"nome":"Imobilizado"}, {"id":146,"nome":"Edificações"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Cultivo e Formação do Solo": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":115,"nome":"Insumos Agrícolas"}, {"id":37,"nome":"Atv. Administrativa"}],
        "CONTROLADOR DUPLO; CAREL; PARA VALVULA DE EXPANSAO": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":134,"nome":"Maquinário Industrial"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Construções de Cercas": [{"id":6,"nome":"Imobilizado"}, {"id":156,"nome":"Construção de Cercas"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Construção Fábrica Itapipoca / Material - 82002": [{"id":6,"nome":"Imobilizado"}, {"id":158,"nome":"Construção Fábrica Itapipoca"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Computadores e Periféricos": [{"id":6,"nome":"Imobilizado"}, {"id":152,"nome":"Computadores e Periféricos"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Combustível e Lubrificantes (Consumo)": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":119,"nome":"Combustível"}, {"id":37,"nome":"Atv. Administrativa"}],
        "COCO VERDE UND": [{"id":1,"nome":"Estoque"}, {"id":42,"nome":"Estoque Matéria Prima"}, {"id":127,"nome":"Etq. Recebimento"}],
        "COCO SECO": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":20,"nome":"Produção"}, {"id":26070,"nome":"Atv. Produtiva"}],
        "Cestas Básicas": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":117,"nome":"Cesta Básica"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Bens de Peq. Valor - 27237": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":130,"nome":"Bens BPV"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Painel Solar - Montagem em Andamento": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":129,"nome":"Energia"}, {"id":51796,"nome":"// FAZENDAS ATACAREJO  /_\\"}],
        "Compras Diretoria - Consumo Pessoal": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":136,"nome":"Consumo Pessoal"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Insumos Pecuários - Manejo e Limpeza": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":123,"nome":"Pecuária"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Insumos Pecuários - Vacinas": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":123,"nome":"Pecuária"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Insumos Pecuários - Alimentos": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":123,"nome":"Pecuária"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Conservação Predial - 20642": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":124,"nome":"Manutenção Prédial"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Informática e Suprimentos - 4184": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":128,"nome":"Informática"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Material de Monitoramento e Segurança - 49740": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":128,"nome":"Informática"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Móveis e Utensílios": [{"id":6,"nome":"Imobilizado"}, {"id":150,"nome":"Móveis e Utensilios"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Veículos": [{"id":6,"nome":"Imobilizado"}, {"id":151,"nome":"Veículos"}, {"id":4875,"nome":"Cadastro de Veiculos"}],
        "Produtos Acabados/Revenda": [{"id":1,"nome":"Estoque"}, {"id":13,"nome":"Estoque de Produtos Acabados"}, {"id":2138,"nome":"Etq. Expedição"}],
        "PALLET DE MADEIRA ( B&P VIA PACK )": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":1,"nome":"Centros de Custos"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Móveis e Utensílios": [{"id":6,"nome":"Imobilizado"}, {"id":150,"nome":"Móveis e Utensilios"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Matéria Prima - Faturamento": [{"id":1,"nome":"Estoque"}, {"id":42,"nome":"Estoque Matéria Prima"}, {"id":127,"nome":"Etq. Recebimento"}],
        "GELAGUA ESMALTEC COLUNA EGC35B BRANCO 220 V": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":136,"nome":"Consumo Pessoal"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Galpão Distribuidora / Serviço": [{"id":6,"nome":"Imobilizado"}, {"id":159,"nome":"Construção Galpão"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Galpão Distribuidora / Material": [{"id":6,"nome":"Imobilizado"}, {"id":159,"nome":"Construção Galpão"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Eventos de Publicidade e Marketing": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":127,"nome":"Eventos"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Despesas de Venda ( Despesas c/ Gerente, etc.)": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":162,"nome":"Despesas de Venda"}, {"id":118,"nome":"Atv. Comercial"}],
        "CAIXA PLASTICA 1000L - 25131": [{"id":1,"nome":"Estoque"}, {"id":57,"nome":"Estoque de Embalagens"}, {"id":127,"nome":"Etq. Recebimento"}],
        "BOMBONA 200L C/ TAMPA": [{"id":1,"nome":"Estoque"}, {"id":57,"nome":"Estoque de Embalagens"}, {"id":127,"nome":"Etq. Recebimento"}],
        "Beneficios / Alimentação": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":3,"nome":"Administração"}, {"id":37,"nome":"Atv. Administrativa"}],
        "Água - Embalagem p/ Acondicionamento": [{"id":3,"nome":"Uso, Consumo ou Desp"}, {"id":3,"nome":"Administração"}, {"id":37,"nome":"Atv. Administrativa"}]
        
    }

    
    dataDeEmissao =  xml_data.find('dhEmi')
    dataDeEmissao = parse_tag_to_string(dataDeEmissao)
    dataDeEmissao = trim_timezone_from_date(dataDeEmissao)

    dataDeVencimento = xml_data.find('dhRecbto')
    dataDeVencimento = parse_tag_to_string(dataDeVencimento)
    dataDeVencimento = trim_timezone_from_date(dataDeVencimento)

    orgId = map_cnpj_to_org_and_user[dest_cnpj]["org"]
    userId = map_cnpj_to_org_and_user[dest_cnpj]["userId"]
    userName = map_cnpj_to_org_and_user[dest_cnpj]["userName"]
    docId = map_series_to_id[series]
    valorProd = products.pop()
    valorProd = parse_tag_to_string(valorProd)

    items = []
    produtos = []
    produtosNaoEncontrados = []

    for i in range(0, len(products),7):
        codAlternativo = parse_tag_to_string(products[i])
        nomeProduto = parse_tag_to_string(products[i+1])
        ncm = parse_tag_to_string(products[i+2])
        siglaUnd = parse_tag_to_string(products[i+3])
        qtd = parse_tag_to_string(products[i+4])
        valorUnitario = parse_tag_to_string(products[i+5])
        valorProduto = parse_tag_to_string(products[i+6])

        unidadeDeMedida = {
            "id":map_unidade[siglaUnd]["id"],
            "nome":map_unidade[siglaUnd]["nome"],
            "sigla":siglaUnd
        }
        
        produtos.append(nomeProduto)
        produto = get_product(codAlternativo, map_unidade[siglaUnd]["id"], nomeProduto, ramifs)
        print("Produto:")
        print(produto)

        try:
            codFornecedor = int(produto.CdFrn.iloc[0])
        except IndexError:
            codFornecedor = 99999
            produtosNaoEncontrados.append(nomeProduto)

        if dest_cnpj == "05635589000118" and codFornecedor == '11533':
            setor = "Power EPI"
        else:
            setor = "Outros"

        finalidade, centroDeCustos, atividade = map_setor[setor]

        if not produto.empty:
            items.append(
                {
                    "id":0,
                    "objeto": {
                        "id":int(produto.iloc[0].Objeto),
                        "nome":nomeProduto
                        },
                    "finalidade":finalidade,
                    "centroDeCustos":centroDeCustos,
                    "atividade":atividade,
                    "unidadeDeMedida":unidadeDeMedida,
                    "quantidadeRecebida": parse_number(qtd),
                    "precoUnitario": parse_number(valorUnitario),
                    "valorBruto": parse_number(valorProduto)
                })

    init()
    print(f"Os seguintes produtos não foram encontrados na(s) ramificação(ões): {", ".join(ramifs.split(' '))}")
    for produtoNaoEncontrado in produtosNaoEncontrados:
        print(f"-{produtoNaoEncontrado}")

    if produtosNaoEncontrados:
        raise Exception(Fore.RED + "Não é possível gerar o arquivo sem encontrar todos os produtos informados no XML!")

    productsJson = {
        "id": 0,
        "dataDaEntrada":dataDeEmissao,
        "dataDeEmissao":dataDeEmissao,
        "organizacao":{"id":orgId,"nome":"empresa"},
        "tipoDeOperacao":{"id":99,"nome":"Compra"},
        "tipoDeDocumento":{"id":docId,"nome":"Nfe Terceiros"},
        "Projeto":{"id":1,"nome":"Documentos"},
        "chaveDoDocumentoEletronico":chaveNFe,
        "fornecedor":{"id":codFornecedor,"nome":"EMPRESAS"},
        "numero":numeroNota,
        "usuarioResponsavel":{"id":userId,"nome":userName},
        "moeda":{"id":1,"nome":"Real"},
        "tipoDeFrete":10,
        "valorDasMercadoriasOuServicos": parse_number(valorProd),
        "itens":items,
        "Titulos":[ 
            {
            "Vencimento": dataDeVencimento,
            "Valor": valorProd,
            "AgenteCobrador": { "id": 21, "nome": "EMPRESAS" },
            "TipoDeCobranca": { "id": 13, "nome": "Boleto"} 
            }
        ]}																	

    jsonList.append(productsJson)



    # with open(f"{numeroNota}", 'w', encoding='utf-8') as f:
    #     json.dump(productsJson, f, ensure_ascii=False, indent=4)

    # print(f"Salvo como: {numeroNota}.json")
    print("*******************************************************************\n")

with open("output.json", "w", encoding='utf-8') as outfile:
    # Loop through the list of JSON objects and write each one to the file
    for json_obj in jsonList:
        json.dump(json_obj, outfile, ensure_ascii=False)
        outfile.write("\n")