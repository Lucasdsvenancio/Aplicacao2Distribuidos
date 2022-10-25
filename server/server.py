from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway, callback, serve
import Pyro5.errors
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime
import threading, time

class Usuario():
    def __init__(self, nome, uri, pk) -> None:
        self.nome = nome
        self.uri = uri
        self.pk = pk
        print(f"N: Usuario {nome} criado")
    
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
        cliente = Proxy(callback)

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

        usuario = Usuario(cliente.get_nome(), callback, pk)
        Servidor.usuarios.append(usuario)

        print(callback)
        cliente.set_public_key(pem)
        cliente.notificar("Cliente cadastrado")
        
    @oneway
    def cadastrar_compromisso(self, callback, evento):
        cliente = Proxy(callback)
        try:
            # Cria compromisso usando o nome do cliente e as informações preenchidas do evento
            compromisso = Compromisso(cliente.get_nome(), evento)
            # Adiciona a lista de compromissos geral
            Servidor.compromissos.append(compromisso)
            # Verifica a existencia de convidados e os convida ao evento
            for convidado in evento["convidados"]:
                # Verifica se o usuário convidado existe e o convida
                res = [user for user in Servidor.usuarios if convidado == user.nome]
                if res != []:
                    # Verifica se o usuário aceita o convite se sim cria outro compromisso com o nome do convidado e adiciona a lista geral
                    usr = Proxy(res[0].uri)
                    print(usr)
                    # Verificar compromisso existente....
                    # Verificar pk
                    aceite = usr.responder(f"{cliente.get_nome()} te chamou para {evento['nome']} as {evento['horario']}hrs aceita? 1 para sim, 0 para não\n")
                    if int(aceite) == 1:
                        tempo_alerta = usr.responder("Tempo de alerta: 0 para não alertar\n")
                        evento['alerta'] = tempo_alerta
                        aux_compromisso = Compromisso(usr.get_nome(), evento)
                        Servidor.compromissos.append(aux_compromisso)

        except Exception:
            print("got an exception from the callback:")
            print("".join(Pyro5.errors.get_pyro_traceback()))

    def cancelar_compromisso(self, callback, evento):
        cliente = Proxy(callback)
        [
            Servidor.compromissos.remove(comp) 
            for comp in Servidor.compromissos 
            if comp.nome_evento == evento and comp.nome == cliente.get_nome()
        ]
        print(len(Servidor.compromissos))
        cliente.notificar("Compromisso excluído")

    def cancelar_alerta(self, callback, evento):
        cliente = Proxy(callback)
        encontrado = [comp for comp in Servidor.compromissos if comp.nome_evento == evento and comp.nome == cliente.get_nome()]
        for e in encontrado:
            e.alerta = 0
            cliente.notificar(f"Evento {e.nome_evento} teve seu alerta cancelado")

    def consultar_compromissos(self, callback, evento):
        cliente = Proxy(callback)
        compromissos = [comp for comp in Servidor.compromissos if comp.nome == cliente.get_nome() and comp.data == evento]
        if compromissos:
            cliente.notificar(f"{len(compromissos)} Eventos encontrados")
            for c in compromissos:
                cliente.notificar(f"Evento {c.nome_evento} - {c.horario}")

    def loop_compromissos(self):
        while True:
            for comp in Servidor.compromissos:
                if comp.alerta > 0:
                    comp.alerta = 0
                    print(f"Compromisso com alerta encontrado: {comp.nome_evento}")
                    

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
