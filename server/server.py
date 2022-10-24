from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway, callback, serve
import Pyro5.errors
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime
import threading, time

class Usuario():
    def __init__(self, nome, ref, pk) -> None:
        self.nome = nome
        self.ref = ref
        self.pk = pk
        print('User created')
    
class Compromisso():
    def __init__(self, nome, evento) -> None:
        self.nome = nome
        self.nome_evento = evento["nome"]
        self.data = evento["data"]
        self.horario = evento["horario"]
        self.alerta = int(evento["alerta"])

@expose
class Servidor(object):
    usuarios = []
    compromissos = []
    
    @oneway
    def cadastro_cliente(self, callback):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        pk = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
        callback._pyroClaimOwnership()
        try:
            usuario = Usuario(callback.get_nome(), callback.get_uri(), pk)
            Servidor.usuarios.append(usuario)
            callback.set_public_key(pem)

        except Exception:
            print("got an exception from the callback:")
            print("".join(Pyro5.errors.get_pyro_traceback()))
        
    @oneway
    def cadastrar_compromisso(self, callback, evento):
        callback._pyroClaimOwnership()
        try:
            compromisso = Compromisso(callback.get_nome(), evento)
            Servidor.compromissos.append(compromisso)
            for convidado in evento["convidados"]:
                print(convidado)

        except Exception:
            print("got an exception from the callback:")
            print("".join(Pyro5.errors.get_pyro_traceback()))
        #Acho que este convidado não precisaria colocar, dava pra apenas mandar para o convidado o request
        #compromisso = Compromisso(referenciaCliente, nome_evento, data, horario, alerta, convidados)
        #compromissos.append(compromisso)

        #return compromisso, podemos enviar os compromissos pro cliente em si, assim a gente pode usar
        # a referencia do cliente como subscriber para que o servidor chame a lista de compromissos daquele usuario

    def cancelar_compromisso(self, referenciaCliente):
        #cancelamento = input("Digite o nome do evento o qual deseja cancelar:")
        #for c in compromissos
            #if c.nome == cancelamento
                # compromissos.pop(c)

        cliente = Proxy(referenciaCliente)
        cliente.notificacao("Compromisso excluído")
    def cancelar_alerta(self, referenciaCliente):
        
        #cancelamento =  input("Qual evento deseja cancelar o alerta ?")
        #for c in compromissos
            #if c.nome == cancelamento
                #c.alerta = 0
                # cliente = Proxy(referenciaCliente)
                # cliente.notificacao("Alerta desativado")
                #break
        pass
    def consultar_compromissos(self, referenciaCliente):
        #data = input("Qual a data a qual deseja pesquisar eventos ?")
        #data = datetime.strptime(data, '%d/%m/%Y').date()
        #for c in compromissos
            #if c.nome == referenciaCliente and c.data == data
                #cliente = Proxy(referenciaCliente)
                #cliente.notificacao("Event infos")

        pass

    def loop_compromissos(self):
        while True:
            for comp in Servidor.compromissos:
                if comp.alerta > 0:
                    print('Evento hoje & alerta ativo')

with Daemon() as daemon:
    print("Starting server")
    ns = locate_ns()
    server = Servidor()
    uri = daemon.register(server)
    ns.register("Agenda", uri)

    loop_thread = threading.Thread(target=server.loop_compromissos)
    loop_thread.daemon = True
    loop_thread.start()

    daemon.requestLoop()
