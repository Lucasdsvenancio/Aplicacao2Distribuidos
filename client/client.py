from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway, callback
import datetime, time, threading, sys, logging

# initialize the logger so you can see what is happening with the callback exception message:
logging.basicConfig(stream=sys.stderr, format="[%(asctime)s,%(name)s,%(levelname)s] %(message)s")
log = logging.getLogger("Pyro5")
log.setLevel(logging.WARNING)

@expose
class Cliente(object):
    def __init__(self, nome):
        self.nome = nome
        self.uri = ""
        self.public_key = ""

    def get_nome(self):
        return self.nome
    
    def get_uri(self):
        return self.uri

    def notificar(self, msg):
        print(f'Mensagem recebida: {msg}')

    def set_public_key(self, public_key):
        Cliente.public_key = public_key
    
    def request_loop(self, daemon):
        daemon.requestLoop()
        time.sleep(10)
    

def cadastro_evento():
    nome_evento = input("Informe o nome do seu evento: ")
    data = input("Informe a data deste evento: ")
    horario = input("Informe as horas que esse evento irá começar: ")
    alerta = input("Deseja ser avisado quanto tempo antes deste evento? caso não deseje apenas digite 0: ")
    convidados = input("Deseja convidar alguém, se sim escreva os nomes: ").split(", ")

    return {"nome":nome_evento, "data":data, "horario":horario, "alerta":alerta, "convidados":convidados}

with Daemon() as daemon:
    # register our callback handler
    print("Bem vindo")
    #Tu ta olhando oq agr ?, que é ruim acompanhar assim
    #Acho que tirar o alerta é o mais fácil de fazer agr
    nome = input("Digite seu nome: ")
    callback = Cliente(nome)
    callback.uri = daemon.register(callback)

    loop_thread = threading.Thread(target=callback.request_loop, args=(daemon, ))
    loop_thread.daemon = False
    loop_thread.start()

    with Proxy("PYRONAME:Agenda") as server:
        # Cria registro do usuário
        server.cadastro_cliente(callback)
        # Cria evento
        evento = cadastro_evento()
        server.cadastrar_compromisso(callback, evento)
        print("Compromisso cadastrado")

    while True:
        time.sleep(5)
    



   