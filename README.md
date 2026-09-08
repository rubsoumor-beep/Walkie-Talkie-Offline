# Walkie-Talkie Offline

Aplicativo de comunicação de voz local desenvolvido em Python,
com transmissão de áudio em tempo real através de UDP.

## Características

- Comunicação offline
- Comunicação pela rede local
- UDP Broadcast
- Áudio PCM 16-bit
- 16 kHz
- Mono
- Interface KivyMD
- Comunicação em tempo real entre dispositivos na mesma rede

## Arquitetura

Microfone
   ↓
Captura de áudio
   ↓
PCM 16-bit / 16 kHz
   ↓
UDP :50055
   ↓
Rede local
   ↓
Outro dispositivo
   ↓
Alto-falante

## Tecnologias

- Python
- Kivy
- KivyMD
- NumPy
- UDP
