from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway, callback
import datetime, time, threading, sys, logging, os

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

    @oneway
    def notificar(self, msg):
        print("\nN: "+msg)
    
    def responder(self, msg):
        return input(msg)

    def resposta_assinada(self, msg):
        pass

    def set_public_key(self, public_key):
        Cliente.public_key = public_key
    
    def request_loop(self, daemon):
        daemon.requestLoop()
        time.sleep(5)
    

def cadastro_evento():
    nome_evento = input("Informe o nome do seu evento: ")
    data = input("Informe a data deste evento: ")
    horario = input("Informe as horas que esse evento irá começar: ")
    alerta = input("Deseja ser avisado quanto tempo antes deste evento? caso não deseje apenas digite 0: ")
    convidados = input("Deseja convidar alguém, se sim escreva os nomes: ").split(", ")

    return {"nome":nome_evento, "data":data, "horario":horario, "alerta":alerta, "convidados":convidados}


if __name__ == "__main__":
    with Daemon() as daemon:
        print("Bem vindo ao cliente")
        nome = input("--> Digite seu nome: ")

        callback = Cliente(nome)
        callback.uri = daemon.register(callback)

        loop_thread = threading.Thread(target=callback.request_loop, args=(daemon, ))
        loop_thread.daemon = False
        loop_thread.start()

        with Proxy("PYRONAME:Agenda") as server:
            # Cadastro do usuário
            server.cadastro_cliente(callback.uri)

            # Cadastro de compromisso
            evento = cadastro_evento()
            server.cadastrar_compromisso(callback.uri, evento)

            # Cancela compromisso
            # cancel_evento = input("Digite o nome do evento a ser cancelado: ")
            # server.cancelar_compromisso(callback.uri, cancel_evento)

            # cancel_alerta = input("Digite o nome do evento a ter seu alerta cancelado: ")
            # server.cancelar_alerta(callback.uri, cancel_alerta)

            checa_evento = input("Digite a data para consulta de eventos: ")
            server.consultar_compromissos(callback.uri, checa_evento)



        while True:
            time.sleep(1)