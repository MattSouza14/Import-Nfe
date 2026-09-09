import pandas as pd
import numpy as np
import re
import json
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from thefuzz import fuzz
from tkinter import Tk  
from tkinter.filedialog import askopenfilename
from colorama import Fore, Back, Style, init
from datetime import datetime

Tk().withdraw()

class XML():
  def __init__(self):
    self.root = ET.Element("nfes")
    self.numberOfDocuments = 0

  def __getitem__(self, key):
    if key in vars(self):
      return vars(self)[key]
    else:
      raise KeyError(f"Element '{key}' not found.")

  def __setitem__(self, key, value):
    if key in vars(self):
      vars(self)[key] = value
    else:
      vars(self).setdefault(key,value)

  def create_document(self):
    self.numberOfDocuments = self.numberOfDocuments + 1
    self.nfe = ET.SubElement(self.root, "nfe", {"numero":str(self.numberOfDocuments)})
    self.fornecedor = ET.SubElement(self.nfe, "fornecedor")
    self.dest = ET.SubElement(self.nfe, "dest")
    self.dhEmi = ET.SubElement(self.nfe, "dhEmi")
    self.dhSaiEnt = ET.SubElement(self.nfe, "dhSaiEnt")
    self.operacao = ET.SubElement(self.nfe, "operacao")
    self.tipoDeDocumento = ET.SubElement(self.nfe, "tipoDeDocumento")
    self.projeto = ET.SubElement(self.nfe, "projeto")
    self.chave = ET.SubElement(self.nfe, "chave")
    self.nNFe = ET.SubElement(self.nfe, "nNFe")
    self.vrCpdMerc = ET.SubElement(self.nfe, "vrCpdMerc")
    self.produtos = ET.SubElement(self.nfe, "produtos")
    self.titulos = ET.SubElement(self.nfe, "titulos")

  def create_node(self, root_name, node_name, node_value):
    if(isinstance(node_value, str)):
      self[node_name] = ET.SubElement(self[root_name], node_name)
      self[node_name].text = node_value
    elif(isinstance(node_value, dict)):
      self[node_name] = ET.SubElement(self[root_name], node_name)
      for key, value in node_value.items():
        self.create_node(node_name, key, value)


  def update(self, name, value):
    self[name].text = value

  def save(self, filename):
    tree = ET.ElementTree(self.root)
    with open(filename, "wb") as files:
        tree.write(files)

def parse_tag_to_string(bs4_tag):
    if bs4_tag:
        remove_tag_regex = r'<\w+>(.*?)</\w+>'
        data = re.search(remove_tag_regex, str(bs4_tag))
        return data.group(1)

def parse_object_name(object_name):
    object_name = str(object_name).strip().lstrip('0')
    parsed_object_name = re.sub(r'\s{2,}', ' ', object_name)
    return parsed_object_name

def convert_date(date_str):
    """
    Convert a date string from DATE_FORMAT_IN to DATE_FORMAT_OUT.

    Args:
        date_str (str): The date string in the input format.

    Returns:
        str: The date string in the output format.
    """
    if not date_str:
      return None

    if len(date_str) == 10:
      DATE_FORMAT_IN = '%Y-%m-%d'
    else:
      DATE_FORMAT_IN = '%Y-%m-%dT%H:%M:%S'
    DATE_FORMAT_OUT = '%d/%m/%Y' 
    # Parse the input date string
    try:
        parsed_date = datetime.strptime(date_str, DATE_FORMAT_IN)
    except ValueError as e:
        return f"Error parsing date: {e}"

    # Format the date to the desired output format
    return parsed_date.strftime(DATE_FORMAT_OUT)
  
def should_ignore_cod_mae(codes_to_check, codes_to_ignore):
  return any(code in codes_to_ignore for code in codes_to_check)

def get_product(cnpj_fornecedor, codigo_alternativo, product_unity, product_name, ramifs):
  produtos_do_fornecedor = df[df['CNPJ']==cnpj_fornecedor]
  ramifs = ramifs.split(' ')

  cod_matches_filter = produtos_do_fornecedor['Alternativo'].apply(lambda cod: str(cod).lstrip("0").replace(" ", "").replace(".", "") == str(codigo_alternativo).lstrip("0").replace(" ", "").replace(".", ""))
  unity_matches_filter = produtos_do_fornecedor['Unidade'].apply(str).apply(lambda df_unity: df_unity == str(product_unity).strip())
  if should_ignore_cod_mae(ramifs, ['47', '20353']):
    cod_mae_matches_filter = True
  else:
    cod_mae_matches_filter = produtos_do_fornecedor['Mae'].apply(lambda cod_mae: parse_object_name(cod_mae) in [parse_object_name(ramif) for ramif in ramifs])
  produtos_do_fornecedor = produtos_do_fornecedor.loc[cod_matches_filter & unity_matches_filter & cod_mae_matches_filter]

  names = pd.DataFrame(columns=["Descricao", "Distancia"])
  names["Descricao"] = produtos_do_fornecedor["Descricao"]
  names["Distancia"] = produtos_do_fornecedor.Descricao.apply(lambda obj: levenshtein_distance(obj, nomeProduto))
  try:
    closest_name = produtos_do_fornecedor["Descricao"]==names.sort_values(by="Distancia").Descricao.iloc[0]
    product = produtos_do_fornecedor[closest_name]

    return product, produtos_do_fornecedor["Imobilizado"].iloc[0].strip() == 'SIM'
  except KeyError:
    print("==============PRODUTO NÃO ENCONTRADO==============")
    print(product_name)

def levenshtein_distance(token1, token2):
    distances = np.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1 - 1] == token2[t2 - 1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]   # Insertion
                b = distances[t1 - 1][t2]   # Deletion
                c = distances[t1 - 1][t2 - 1] # Substitution
                distances[t1][t2] = min(a, b, c) + 1

    return int(distances[len(token1)][len(token2)])
    
def parse_number(number):
    number = float(number)
    if int(number) - number != 0:
        return number
    else:
        return int(number)    

def trim_timezone_from_date(date_str):
    return date_str[:-6]

def format_cnpj(cnpj):
  cnpj = str(cnpj)
  size = len(cnpj)
  diff = 14 - size

  return '0' * diff + cnpj 

def get_unity_id(siglaUnd):
  unity = {"id":0,"nome":""}
  try:
    unity = map_unidade[siglaUnd]
  except KeyError:
    print(f"Unidade {siglaUnd} não encontrada, mas você pode incluí-la agora!\n")
    code = input("Digite o código interno da unidade no TopManager: ")
    name = input("Digite o nome da unidade: ")
    map_unidade[siglaUnd] = {"id":str(code),"nome":name}
    unity = get_unity_id(siglaUnd)
  return unity

map_fazendas_101296 = {
    "51799": "Fazenda Aguape",
    "94328": "FAZENDA YPIOCA INDUSTRIAL",
    "51800": "Fazenda Catirina",
    "51797": "Fazenda São Gabriel",
    "53143": "Fazenda Acaraú",
    "51808": "Fazenda Boa Esperança",
    "51801": "Fazenda Bonfim",
    "84021": "Fazenda Pedra Atravessada",
    "84022": "Fazenda Riachão",
    "86439": "Fazenda Caiçarinha",
    "84036": "Fazenda Calumbi",
    "84023": "Fazenda Dona Maria",
    "83345": "Fazenda Ypioca",
    "83976": "Fazenda Ameixas",
    "83984": "Fazenda Lagoa das Merces",
    "83985": "Fazenda Roncador",
    "83986": "Fazenda Timbaúba",
    "83987": "Fazenda Dona Severina",
    "83974": "Fazenda São José",
    "87679": "Fazenda Acácio",
    "52914": "Fazenda Arco Verde",
    "52920": "Fazenda Guaribas",
    "52951": "Fazenda Olho Agua do Salvador",
    "54853": "Fazenda Vázea do Mundaú",
    "56077": "Fazenda Consceara",
    "74794": "Terreno Malamba",
    "79252": "Terreno Calumbi",
}

_fazenda_escolhida_cache = None

def reset_fazenda_cache():
  global _fazenda_escolhida_cache
  _fazenda_escolhida_cache = None

def select_fazenda_101296():
  global _fazenda_escolhida_cache
  if _fazenda_escolhida_cache is not None:
    return _fazenda_escolhida_cache

  fazendas_list = list(map_fazendas_101296.items())
  print("\nSelecione a fazenda (atividade) para a ramificação 101296:")
  for idx, (codigo, nome) in enumerate(fazendas_list, start=1):
    print(f"{idx:2d} - {nome} (cód. {codigo})")

  while True:
    escolha = input("Digite o número da fazenda desejada: ").strip()
    if escolha.isdigit() and 1 <= int(escolha) <= len(fazendas_list):
      codigo, nome = fazendas_list[int(escolha) - 1]
      _fazenda_escolhida_cache = {"id": codigo, "nome": nome}
      return _fazenda_escolhida_cache
    print("Opção inválida, tente novamente.")

map_cnpj_to_org_and_user = {
    "02974336000180": {"org": "2", "userId": "334", "userName": "Carlos_Eduardo"}, #Malibru Matriz
    "02974336000342": {"org": "18", "userId": "334", "userName": "Carlos_Eduardo"}, #Malibru Dist
    "02974336000504": {"org": "21", "userId": "334", "userName": "Carlos_Eduardo"}, #Malibru Santos Dumont
    "05635589000118": {"org": "16", "userId": "403", "userName": "Cristyan Rodrigues"}, #Dicoco Ceará
    "05635589000207": {"org": "17", "userId": "403", "userName": "Cristyan Rodrigues"}, #Dicoco Petrolândia
    "05635589000380": {"org": "20", "userId": "403", "userName": "Cristyan Rodrigues"}, #Dicoco Itapipoca
    "23487846000101": {"org": "23", "userId": "334", "userName": "Carlos_Eduardo"}, #Atacarejo Matriz
    "23487846000284": {"org": "25", "userId": "334", "userName": "Carlos_Eduardo"}, #Atacarejo Itarema
    "23487846000365": {"org": "26", "userId": "334", "userName": "Carlos_Eduardo"}, #Atacarejo Camocim
    "23487846000446": {"org": "29", "userId": "334", "userName": "Carlos_Eduardo"}, #Atacarejo Itapipoca
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
    "BAMBONA":{"id": "68", "nome": "Bambona"},
    "ARR":{"id": "1", "nome": "Unidade"},
    "BD":{"id": "64", "nome": "Balde"},
    "BB":{"id": "64", "nome": "Balde"},
    "Bl":{"id": "64", "nome": "Balde"},
    "BL":{"id": "66", "nome": "Bloco"},
    "BT":{"id": "1105", "nome": "Blister"},
    "BO":{"id": "67", "nome": "Bobina"},
    "BR":{"id": "1099", "nome": "Barra"},
    "CAIXA":{"id": "37", "nome": "Caixa"},
    "CX":{"id": "37", "nome": "Caixa"},
    "CART":{"id": "1089", "nome": "Cartela"},
    "CT":{"id": "65", "nome": "Cento"},
    "CENTO":{"id": "65", "nome": "Cento"},
    "cto":{"id": "65", "nome": "Cento"},
    "DC":{"id": "1079", "nome": "Direcionador de Custo"},
    "DS":{"id": "1100", "nome": "DOSE"},
    "FARDO":{"id": "39", "nome": "Fardo"},
    "FD":{"id": "39", "nome": "Fardo"},
    "fdo":{"id": "39", "nome": "Fardo"},
    "FL":{"id": "1103", "nome": "Fileira"},
    "CJ":{"id": "1104", "nome": "Conjunto"},
    "FR":{"id": "1080", "nome": "Frasco"},
    "FC":{"id": "1080", "nome": "Frasco"},
    "GL":{"id": "63", "nome": "Galão"},
    "gal":{"id": "63", "nome": "Galão"},
    "GR":{"id": "9", "nome": "Grama"},
    "GRF":{"id": "26", "nome": "Garrafa"},
    "H":{"id": "1088", "nome": "Hora"},
    "JG":{"id": "1097", "nome": "Jogo"},
    "KTS":{"id": "1098", "nome": "Kit"},
    "KIT":{"id": "1098", "nome": "Kit"},
    "KG":{"id": "2", "nome": "Quilograma"},
    "Kg":{"id": "2", "nome": "Quilograma"},
    "Km":{"id": "58", "nome": "Quilômetro"},
    "KW":{"id": "7", "nome": "Quilowatt hora"},
    "LITRO":{"id": "3", "nome": "Litro"},
    "LTO":{"id": "1094", "nome": "Litro"},
    "LT":{"id": "1094", "nome": "Litro"},
    "L":{"id": "1094", "nome": "Litro"},
    "LTA":{"id": "1101", "nome": "Lata"},
    "M2":{"id": "5", "nome": "Metro quadrado"},
    "MET":{"id": '5', "nome": "Metro quadrado"},
    "M3":{"id": "6", "nome": "Metro cúbico"},
    "MIL":{"id": "13", "nome": "Milheiro"},
    "MT":{"id": "4", "nome": "Metro linear"},
    "M":{"id": "4", "nome": "Metro linear"},
    "PCS":{"id": "1086", "nome": "Peça"},
    "PEC":{"id": "1086", "nome": "Peça"},
    "PEÇ":{"id": "1086", "nome": "Peça"},
    "PCA":{"id": "1086", "nome": "Peça"},
    "PC":{"id": "1086", "nome": "Peça"},
    "Pc":{"id": "1086", "nome": "Peça"},
    "PCT":{"id": "34", "nome": "Pacote"},
    "pct":{"id": "34", "nome": "Pacote"},
    "PCT":{"id": "34", "nome": "Pacote"},
    "PT":{"id": "34", "nome": "Pacote"},
    "PL":{"id": "1091", "nome": "Paletes"},
    "PR":{"id": "71", "nome": "Par"},
    "PAR":{"id": "71", "nome": "Par"},
    "QT":{"id": "72", "nome": "Quarto"},
    "RL":{"id": "40", "nome": "Rolo"},
    "ROL":{"id": "40", "nome": "Rolo"},
    "RS":{"id": "69", "nome": "Resma"},
    "SC":{"id": "1093", "nome": "Saco"},
    "TAMBOR":{"id": "18", "nome": "Tambor"},
    "TB":{"id": "70", "nome": "Tubo"},
    "T":{"id": "28", "nome": "Tonelada"},
    "TO":{"id": "28", "nome": "Tonelada"},
    "TON":{"id": "28", "nome": "Tonelada"},
    "Ton":{"id": "28", "nome": "Tonelada"},
    "UN":{"id": "1", "nome": "Unidade"},
    "AM1":{"id": "1", "nome": "Unidade"},
    "Un":{"id": "1", "nome": "Unidade"},
    "und":{"id": "1", "nome": "Unidade"},
    "Um":{"id": "1", "nome": "Unidade"},
    "UND":{"id": "1", "nome": "Unidade"},
    "UNI":{"id": "1", "nome": "Unidade"},
    "UNID":{"id": "1", "nome": "Unidade"},
    "un":{"id": "1", "nome": "Unidade"},
    "VR":{"id": "1102", "nome": "Volumes"},
    "VL":{"id": "59", "nome": "Volumes"},
    "CAR":{"id": "1095", "nome": "Carrada"},
    "KT":{"id": "1098", "nome": "KIT"}
}


map_setor = {
    "Power EPI": [{"id":"1","nome":"Estoque"}, {"id":"6","nome":"Almoxarifado"}, { "id":"79","nome":"Etq. Recebimento"}],
    "Imobilizado": [{"id":"6","nome":"Imobilizado"}, {"id":"3","nome":"Administração"}, {"id":"37","nome":"Atv. Administrativa"}],
    "Outros": [{"id":"3","nome":"Uso, Consumo ou Desp"}, {"id":"3","nome":"Administração"}, {"id":"37","nome":"Atv. Administrativa"}],
    "21167": [{"id": "3", "nome": "Uso, Consumo ou Desp"},{"id": "18", "nome": "Logistica"}, {"id": "37", "nome": "Atv. Administrativa"}],
    "21167": [{"id": "3", "nome": "Uso, Consumo ou Desp"},{"id": "18", "nome": "Logistica"}, {"id": "4876", "nome": "Placas - Linha Normal"}],
    "101296": [{"id": 3, "nome": "Uso, Consumo ou Desp"}, {"id": "173", "nome": "Casa de Apoio"}, None],  # TODO: preencher finalidade/centroDeCustos reais
}

CNPJs = ['05635589000118', '05635589000207', '02974336000342']

filenames = askopenfilename(multiple=True) 
columns = ["Alternativo","Objeto", "Descricao","CNPJ","CdFrn","NomeFrn", "Unidade", "Mae", "Imobilizado"]
df = pd.read_excel('prod.xlsx', header=None, names=columns, skiprows=list(range(4)))
df["Descricao"] = df["Descricao"].apply(lambda x: x.split(" - Cód.")[0])
df['CNPJ'] = df['CNPJ'].apply(format_cnpj)
df["Alternativo"] = df["Alternativo"].apply(str).apply(str.strip)

docs = []
nfes = XML()
for filename in filenames:
  print("*******************************************************************")
  print(f"Gerando arquivo da nota {filename.split('/')[-1].split('.')[0]}")
  ramifs = input("Digite o(s) código(s) da(s) ramificação(ões) dos objetos dessa nota.\nSepare os códigos digitados por um espaço em branco: ")
  reset_fazenda_cache()  
  with open(filename, 'r', encoding='utf-8') as f:
    data = f.read()

  xml_data = BeautifulSoup(data, "xml")

  dataDeEmissao =  xml_data.find('dhEmi')
  dataDeEmissao = parse_tag_to_string(dataDeEmissao)
  dataDeEmissao = trim_timezone_from_date(dataDeEmissao)
  dataDeEmissao = convert_date(dataDeEmissao)

  dataDeEntrada =  xml_data.find('dhSaiEnt')
  if dataDeEntrada:
    dataDeEntrada = parse_tag_to_string(dataDeEntrada)
    dataDeEntrada = trim_timezone_from_date(dataDeEntrada)
    dataDeEntrada = convert_date(dataDeEntrada)
  else:
    dataDeEntrada = dataDeEmissao

  dataDeVencimento = xml_data.find('dVenc')
  if dataDeVencimento:
    dataDeVencimento = parse_tag_to_string(dataDeVencimento)
    dataDeVencimento = convert_date(dataDeVencimento)
  else:
    dataDeVencimento = dataDeEmissao

  xml_products = xml_data.find_all('det')

  chaveNFe = xml_data.find(['chNFe'])
  chaveNFe = parse_tag_to_string(chaveNFe)

  forn_cnpj = chaveNFe[6:20]
  codFornecedor = str(df[df["CNPJ"]==forn_cnpj].CdFrn.iloc[0])

  dest_cnpj = xml_data.find('dest').find('CNPJ')
  dest_cnpj = parse_tag_to_string(dest_cnpj)

  numeroNota = xml_data.find('nNF')
  numeroNota = parse_tag_to_string(numeroNota)

  series = xml_data.find('serie')
  series = parse_tag_to_string(series)

  valorFrete = xml_data.find('vFrete')
  valorFrete = parse_tag_to_string(valorFrete)

  valorDescontoNota = xml_data.find('total').find('vDesc')
  valorDescontoNota = parse_tag_to_string(valorDescontoNota)

  valorDesoneradoNota = xml_data.find('total').find('vICMSDeson')
  valorDesoneradoNota = parse_tag_to_string(valorDesoneradoNota)

  valorMercadoria = xml_data.find('total').find('vProd')
  valorMercadoria = parse_tag_to_string(valorMercadoria)
  valorMercadoria = str(float(valorMercadoria) - float(valorDescontoNota) - float(valorDesoneradoNota))
  
  valorNota = xml_data.find('total').find('vNF')
  valorNota = parse_tag_to_string(valorNota)

  orgId = map_cnpj_to_org_and_user[dest_cnpj]["org"]
  userId = map_cnpj_to_org_and_user[dest_cnpj]["userId"]
  userName = map_cnpj_to_org_and_user[dest_cnpj]["userName"]
  docId = map_series_to_id[series]

  json_products = []
  produtos = []
  produtosNaoEncontrados = []

  for xml_product in xml_products:
    codAlternativo = parse_tag_to_string(xml_product.find('cProd'))
    nomeProduto = parse_tag_to_string(xml_product.find('xProd'))
    ncm = parse_tag_to_string(xml_product.find('NCM'))
    siglaUnd = parse_tag_to_string(xml_product.find('uCom'))
    qtd = parse_tag_to_string(xml_product.find('qCom'))
    valorUnitario = parse_tag_to_string(xml_product.find('vUnCom'))
    valorProduto = parse_tag_to_string(xml_product.find('vProd'))
    valorDesonerado = parse_tag_to_string(xml_product.find('vICMSDeson')) or '0'
    valorDesconto = parse_tag_to_string(xml_product.find('vDesc')) or '0'
    valorFrete = parse_tag_to_string(xml_product.find('vFrete')) or '0'
    valorIPI = parse_tag_to_string(xml_product.find('vIPI')) or '0'
    valorDespAce = parse_tag_to_string(xml_product.find('vOutro')) or '0'

    unity = get_unity_id(siglaUnd)
    unidadeDeMedida = {
      "id":str(unity["id"]),
      "nome":unity["nome"],
      "sigla":siglaUnd
    }
    
    produtos.append(nomeProduto)
    try:
      produto, produtoEImobilizado = get_product(forn_cnpj, codAlternativo, unity["id"], nomeProduto, ramifs)
    except KeyError:
      produtosNaoEncontrados.append(nomeProduto)

    if dest_cnpj == "05635589000118" and codFornecedor == '11533':
      setor = "Power EPI"
    else:
      if produtoEImobilizado:
        setor = "Imobilizado"
      elif "101296" in ramifs.split(' '):  
        setor = "101296"
      elif "22167" in ramifs.split(' '):    
        setor = "22167"
      else:
        setor = "Outros"

    finalidade, centroDeCustos, atividade = map_setor[setor]

    if setor == "101296":
      atividade = select_fazenda_101296()  

    if not produto.empty:
      json_products.append(
        {
          "objeto":str(produto.iloc[0].Objeto),
          "unidadeDeMedida":unidadeDeMedida,
          "finalidade":finalidade,
          "centroDeCustos":centroDeCustos,
          "atividade":atividade,
          "quantidadeRecebida": qtd,
          "precoUnitario": valorUnitario,
          "valorBruto": valorProduto,
          "valorDesconto": str(float(valorDesconto) + float(valorDesonerado)) ,
          "valorFrete": valorFrete,
          "valorIPI": valorIPI,
          "valorDespAce": valorDespAce
        })

  nfes.create_document()
  nfes.create_node("fornecedor","cnpj",forn_cnpj)
  nfes.create_node("fornecedor","codigo",codFornecedor)
  nfes.create_node("dest","cnpj",dest_cnpj)
  nfes.create_node("dest","codigo",orgId)

  nfes.update("dhEmi",dataDeEmissao)
  nfes.update("dhSaiEnt",dataDeEntrada)
  nfes.update("operacao","99")
  nfes.update("tipoDeDocumento",docId)
  nfes.update("projeto","1")
  nfes.update("chave",chaveNFe)
  nfes.update("nNFe",numeroNota)
  nfes.update("vrCpdMerc",valorMercadoria)

  nfes.create_node("titulos", "vencimento", dataDeVencimento)
  nfes.create_node("titulos", "valor", valorNota)

  for json_product in json_products:
    nfes.create_node("produtos","produto", json_product)

nfes.save(f"output.xml")