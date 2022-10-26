from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway, callback
import datetime, time, threading, sys, logging, os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64

def decode64(str):
    return base64.b64decode(str)

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
        print(msg)
    
    def responder(self, msg):
        return input(msg)

    def resposta_assinada(self, sign, msg):
        loaded_public_key = ed25519.Ed25519PublicKey.from_public_bytes(decode64(Cliente.public_key))
        sign = decode64(sign)
        byte_msg = msg.encode()
        try:
            loaded_public_key.verify(sign, byte_msg)
            resposta = self.responder(msg)
            return resposta
        except:
            print("Verification failed!")

    def set_public_key(self, public_bytes):
        Cliente.public_key = public_bytes
    
    def request_loop(self, daemon):
        daemon.requestLoop()
        time.sleep(2)
    

def cadastro_evento():
    nome_evento = input("Informe o nome do seu evento: ")
    data = input("Informe a data deste evento, formato dd/mm/YYYY HH:MM: ")
    alerta = input("Deseja ser avisado quanto tempo antes deste evento? caso não deseje apenas digite 0: ")
    convidados = input("Deseja convidar alguém, se sim escreva os nomes: ").split(", ")

    return {"nome":nome_evento, "data":data, "alerta":alerta, "convidados":convidados}


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
            while True: 
                print("--------------------------------")
                print("1-Cadastrar Evento\n2-Cancelar Evento\n3-Cancelar Alerta\n4-Consultar Compromissos")
                option = int(input(""))
                if option == 1:
                 # Cadastro de compromisso
                    evento = cadastro_evento()
                    server.cadastrar_compromisso(callback.uri, evento)
                elif option == 2:
                    # Cancela compromisso
                    cancel_evento = input("Digite o nome do evento a ser cancelado: ")
                    server.cancelar_compromisso(callback.uri, cancel_evento)
                elif option == 3:
                # Cancela alerta
                    cancel_alerta = input("Digite o nome do evento a ter seu alerta cancelado: ")
                    server.cancelar_alerta(callback.uri, cancel_alerta)
                elif option == 4:
                # Consulta compromisso
                    checa_evento = input("Digite a data para consulta de eventos, formato dd/mm/YYYY: ")
                    server.consultar_compromissos(callback.uri, checa_evento)
                else:
                    while True:
                        time.sleep(1)