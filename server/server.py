from Pyro5.api import Daemon, Proxy, locate_ns, expose, oneway
import Pyro5.errors
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64
from datetime import date, datetime
import threading, time

def encode64(bytes):
    return base64.b64encode(bytes).decode(encoding="utf-8")

class Usuario():
    def __init__(self, nome, uri, private_key) -> None:
        self.nome = nome
        self.uri = uri
        self.private_key = private_key
        print(f"N: Usuario {nome} criado")
    
class Compromisso():
    def __init__(self, nome, evento) -> None:
        self.nome = nome
        self.nome_evento = evento["nome"]
        self.data = evento["data"]
        self.alerta = int(evento["alerta"])
        self.alertado = 0

@expose
class Servidor(object):
    usuarios = []
    compromissos = []
    
    @oneway
    def cadastro_cliente(self, callback):
        cliente = Proxy(callback)

        private_key = ed25519.Ed25519PrivateKey.generate()

        public_key = private_key.public_key()

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        usuario = Usuario(cliente.get_nome(), callback, private_key)
        Servidor.usuarios.append(usuario)

        cliente.set_public_key(encode64(public_bytes))
        cliente.notificar("Cliente cadastrado")
        
    @oneway
    def cadastrar_compromisso(self, callback, evento):
        cliente = Proxy(callback)
        try:
            compromisso = Compromisso(cliente.get_nome(), evento)
            Servidor.compromissos.append(compromisso)
            
            for convidado in evento["convidados"]:
                res = [user for user in Servidor.usuarios if convidado == user.nome]

                if res != []:
                    usr = Proxy(res[0].uri)
                    
                    msg = f"{cliente.get_nome()} te chamou para {evento['nome']} as {evento['horario']}hrs aceita? 1 para sim, 0 para não\n"
                    signature = res[0].private_key.sign(msg.encode())
                    verifica = usr.resposta_assinada(encode64(signature), msg)
                    if int(verifica) == 1: 
                        tempo_alerta = usr.responder("Tempo de alerta: 0 para não alertar\n")
                        evento['alerta'] = tempo_alerta
                        aux_compromisso = Compromisso(usr.get_nome(), evento)
                        Servidor.compromissos.append(aux_compromisso)
        except Exception:
            print("got an exception from the callback:")
            print("".join(Pyro5.errors.get_pyro_traceback()))


    @oneway
    def cancelar_compromisso(self, callback, evento):
        cliente = Proxy(callback)
        [
            Servidor.compromissos.remove(comp) 
            for comp in Servidor.compromissos 
            if comp.nome_evento == evento and comp.nome == cliente.get_nome()
        ]
        print(len(Servidor.compromissos))
        cliente.notificar("Compromisso excluído")

    @oneway
    def cancelar_alerta(self, callback, evento):
        cliente = Proxy(callback)
        encontrado = [comp for comp in Servidor.compromissos if comp.nome_evento == evento and comp.nome == cliente.get_nome()]
        for e in encontrado:
            e.alerta = 0
            cliente.notificar(f"Evento {e.nome_evento} teve seu alerta cancelado")

    @oneway
    def consultar_compromissos(self, callback, evento):
        cliente = Proxy(callback)
        compromissos = [comp for comp in Servidor.compromissos if comp.nome == cliente.get_nome() and datetime.strptime(comp.data, "%d/%m/%Y %H:%M").date().strftime("%d/%m/%Y") == evento]
        if compromissos:
            cliente.notificar(f"{len(compromissos)} Eventos encontrados")
            for c in compromissos:
                cliente.notificar(f"Evento {c.nome_evento} - {c.data}")


    def loop_compromissos(self):
        while True:
            for c in Servidor.compromissos:
                if c.alertado == 0:
                    now = datetime.now().timestamp()
                    horario = datetime.strptime(c.data, "%d/%m/%Y %H:%M").timestamp()
                    if (horario - now)/ 60 <= c.alerta:
                        user = [usr for usr in Servidor.usuarios if usr.nome == c.nome]
                        cliente = Proxy(user[0].uri)
                        cliente.notificar(f"Voce tem um compromisso daqui {c.alerta} minutos")
                        c.alertado = 1

                    

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
