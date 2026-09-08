import socket
import threading
import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np

# Configurações padrões otimizadas para ZERAR O DELAY
FREQUENCIA = 16000
BUFFER_SIZE = 256  # Reduzido de 1024 para 256 para pacotes ultra rápidos
PORTA_PADRAO = 50055
FATOR_GANHO = 3.0  # Multiplica o volume do microfone por 3 (Ajuste aqui se precisar)


class SistemaVozUnificado:
    def __init__(self, janela_principal):
        self.janela = janela_principal
        self.janela.title("Sistema de Voz UDP v1.1 - Broadcast")
        self.janela.geometry("350x300")
        self.janela.resizable(False, False)

        # Variáveis de controle de estado
        self.rodando = False

        # --- CONFIGURAÇÃO DO SOCKET DE ENVIO COM PERMISSÃO DE BROADCAST ---
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.stream_entrada = None
        self.stream_saida = None

        # --- INTERFACE VISUAL (Campos e Botões) ---

        tk.Label(self.janela, text="Endereço IP de Destino:", font=("Arial", 10, "bold")).pack(pady=(15, 2))
        self.campo_ip = tk.Entry(self.janela, font=("Arial", 11), justify="center", width=20)

        # IP de transmissão universal (Mude para 127.255.255.255 se for testar sozinho no mesmo PC)
        self.campo_ip.insert(0, "255.255.255.255")
        self.campo_ip.pack(pady=5)

        self.btn_controle = tk.Button(self.janela, text="LIGAR SISTEMA", bg="#107C41", fg="white",
                                      font=("Arial", 12, "bold"), width=20, height=2, command=self.alternar_sistema)
        self.btn_controle.pack(pady=20)

        self.lbl_status = tk.Label(self.janela, text="Status: Sistema Desconectado", fg="red",
                                   font=("Arial", 10, "italic"))
        self.lbl_status.pack(pady=10)

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar_aplicativo)

    def thread_receptor(self):
        """Atua como o Servidor/Receptor: Escuta a porta de rede e aceita transmissões em massa"""
        socket_escuta = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            socket_escuta.bind(("0.0.0.0", PORTA_PADRAO))
        except Exception as e:
            messagebox.showerror("Erro de Rede", f"Não foi possível abrir a porta {PORTA_PADRAO}.\n{e}")
            self.desligar_recursos()
            return

        while self.rodando:
            try:
                dados_brutos, _ = socket_escuta.recvfrom(BUFFER_SIZE * 2)
                if dados_brutos and self.stream_saida:
                    audio_convertido = np.frombuffer(dados_brutos, dtype='int16')
                    self.stream_saida.write(audio_convertido)
            except:
                break
        socket_escuta.close()

    def callback_emissor(self, indata, frames, time, status):
        """Atua como o Emissor: Captura os blocos do microfone, amplifica e dispara no espaço"""
        if self.rodando:
            ip_destino = self.campo_ip.get().strip()
            try:
                # AMPLIFICADOR DIGITAL: Multiplica os dados da matriz pelo fator de ganho
                audio_amplificado = indata.astype(np.float32) * FATOR_GANHO

                # Evita distorção digital travando os limites máximos e mínimos do int16
                audio_recortado = np.clip(audio_amplificado, -32768, 32767).astype(np.int16)

                # Despacha os bytes gerados pelo som amplificado
                self.socket_udp.sendto(audio_recortado.tobytes(), (ip_destino, PORTA_PADRAO))
            except:
                pass

    def alternar_sistema(self):
        if not self.rodando:
            if not self.campo_ip.get().strip():
                messagebox.showwarning("Aviso", "Por favor, digite um endereço IP válido.")
                return

            self.rodando = True
            self.btn_controle.config(text="DESLIGAR SISTEMA", bg="#A80000")
            self.lbl_status.config(text="Status: Transmitindo e Ouvindo...", fg="green")

            try:
                # Inicializa a saída de áudio com latência ultra baixa (ignora a fila do Windows)
                self.stream_saida = sd.OutputStream(
                    samplerate=FREQUENCIA,
                    channels=1,
                    dtype='int16',
                    blocksize=BUFFER_SIZE,
                    latency='low'
                )
                self.stream_saida.start()

                threading.Thread(target=self.thread_receptor, daemon=True).start()

                # Inicializa o microfone forçando o canal 0 e latência ultra baixa
                self.stream_entrada = sd.InputStream(
                    samplerate=FREQUENCIA,
                    channels=1,
                    dtype='int16',
                    blocksize=BUFFER_SIZE,
                    callback=self.callback_emissor,
                    device=0,
                    latency='low'
                )
                self.stream_entrada.start()

                messagebox.showinfo("Sucesso", "Modo rádio geral ativado com sucesso!")

            except Exception as e:
                messagebox.showerror("Erro de Inicialização",
                                     f"Falha ao acessar o hardware de áudio.\n{e}")
                self.desligar_recursos()
        else:
            self.desligar_recursos()
            messagebox.showinfo("Sistema", "Conexões encerradas com segurança.")

    def desligar_recursos(self):
        self.rodando = False
        self.btn_controle.config(text="LIGAR SISTEMA", bg="#107C41")
        self.lbl_status.config(text="Status: Sistema Desconectado", fg="red")

        if self.stream_entrada:
            try:
                self.stream_entrada.close()
            except:
                pass
            self.stream_entrada = None

        if self.stream_saida:
            try:
                self.stream_saida.close()
            except:
                pass
            self.stream_saida = None

    def fechar_aplicativo(self):
        self.rodando = False
        self.desligar_recursos()
        self.janela.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaVozUnificado(root)
    root.mainloop()
