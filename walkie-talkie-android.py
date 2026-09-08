import socket
import threading
import numpy as np
import sounddevice as sd

# Configurações do motor de áudio e rede (idênticas ao seu .exe)
FREQUENCIA = 16000
BUFFER_SIZE = 256
PORTA_PADRAO = 50055

# Componentes da Interface Android (Kivy)
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock


class AppWalkieTalkieAndroid(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.rodando = False

        # Configuração do Socket UDP com Permissão de Broadcast
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.stream_entrada = None
        self.stream_saida = None

        # --- LAYOUT DA TELA DO CELULAR ---
        layout = MDBoxLayout(orientation='vertical', padding=30, spacing=20)

        # Título
        layout.add_widget(MDLabel(
            text="Rádio Walkie-Talkie Offline",
            font_style="H5",
            halign="center",
            bold=True
        ))

        # Campo de Texto para o IP (Padrão Broadcast)
        self.campo_ip = MDTextField(
            text="255.255.255.255",
            hint_text="Endereço IP de Destino",
            helper_text="Mantenha em 255.255.255.255 para falar geral",
            helper_text_mode="on_focus",
            align="center",
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5}
        )
        layout.add_widget(self.campo_ip)

        # Botão Principal de Conexão
        self.btn_controle = MDRaisedButton(
            text="LIGAR SISTEMA",
            size_hint=(0.8, None),
            height="60dp",
            pos_hint={"center_x": 0.5},
            md_bg_color=(16 / 255, 124 / 255, 65 / 255, 1),  # Verde original do seu .exe
            on_release=self.alternar_sistema
        )
        layout.add_widget(self.btn_controle)

        # Status do Aplicativo
        self.lbl_status = MDLabel(
            text="Status: Desconectado",
            halign="center",
            theme_text_color="Hint"
        )
        layout.add_widget(self.lbl_status)

        return layout

    def thread_receptor(self):
        socket_escuta = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            socket_escuta.bind(("0.0.0.0", PORTA_PADRAO))
        except:
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
        if self.rodando:
            ip_destino = self.campo_ip.text.strip()
            try:
                # Mantém o seu amplificador digital calibrado (Fator 3.0)
                audio_amplificado = indata.astype(np.float32) * 3.0
                audio_recortado = np.clip(audio_amplificado, -32768, 32767).astype(np.int16)
                self.socket_udp.sendto(audio_recortado.tobytes(), (ip_destino, PORTA_PADRAO))
            except:
                pass

    def alternar_sistema(self, instance):
        if not self.rodando:
            self.rodando = True
            self.btn_controle.text = "DESLIGAR SISTEMA"
            self.btn_controle.md_bg_color = (168 / 255, 0, 0, 1)  # Vermelho
            self.lbl_status.text = "Status: Transmitindo e Ouvindo..."

            try:
                self.stream_saida = sd.OutputStream(samplerate=FREQUENCIA, channels=1, dtype='int16',
                                                    blocksize=BUFFER_SIZE, latency='low')
                self.stream_saida.start()

                threading.Thread(target=self.thread_receptor, daemon=True).start()

                # No Android, omitimos o 'device=0' para o sistema usar o microfone padrão do celular automaticamente
                self.stream_entrada = sd.InputStream(samplerate=FREQUENCIA, channels=1, dtype='int16',
                                                     blocksize=BUFFER_SIZE, callback=self.callback_emissor,
                                                     latency='low')
                self.stream_entrada.start()
            except Exception as e:
                self.alternar_sistema(None)
        else:
            self.rodando = False
            self.btn_controle.text = "LIGAR SISTEMA"
            self.btn_controle.md_bg_color = (16 / 255, 124 / 255, 65 / 255, 1)
            self.lbl_status.text = "Status: Desconectado"

            if self.stream_entrada: self.stream_entrada.close()
            if self.stream_saida: self.stream_saida.close()

    def on_stop(self):
        """Garante o desligamento do microfone se o usuário fechar o app puxando a tela do celular"""
        self.rodando = False
        if self.stream_entrada: self.stream_entrada.close()
        if self.stream_saida: self.stream_saida.close()


if __name__ == "__main__":
    AppWalkieTalkieAndroid().run()