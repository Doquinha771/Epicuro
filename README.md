# Epicuro

Epicuro é um gerenciador desktop para baixar vídeos, áudios e playlists em uma fila única. A interface foi feita em PySide6 e o processamento usa yt-dlp, FFmpeg e SpotDL.

## O que tem no app

- fila de downloads com iniciar, pausar, cancelar e reorganizar;
- vídeo em MP4 e áudio em MP3;
- suporte a playlists e links do Spotify;
- progresso, velocidade e tempo restante;
- biblioteca dos arquivos concluídos;
- arrastar arquivos da biblioteca direto para o Explorer, Área de Trabalho ou outro programa;
- pesquisa nas transferências e na biblioteca;
- pasta de downloads configurável;
- ferramentas para verificar componentes, copiar diagnóstico e limpar downloads incompletos;
- build para Windows sem janela de terminal.

## Rodar pelo código-fonte

Requer Windows 10 ou 11 e Python 3.11 ou mais recente.

1. Baixe ou clone o repositório.
2. Abra `INICIAR_EPICURO.bat`.
3. Na primeira execução, o script cria `.venv` e instala as dependências.
4. Depois disso, o Epicuro abre usando `pythonw.exe`, sem deixar um terminal aberto atrás do app.

Também existe `INICIAR_EPICURO_SILENCIOSO.vbs` para iniciar todo o processo sem mostrar a janela do CMD.

## Como usar

1. Clique em **Novo link** ou use `Ctrl+N`.
2. Cole o endereço do vídeo, música ou playlist.
3. Escolha o formato e a qualidade.
4. Confirme para adicionar à fila.
5. Os arquivos concluídos aparecem na **Biblioteca**.

Atalhos úteis:

- `Ctrl+Shift+V` usa o link que estiver copiado;
- `Ctrl+Enter` inicia ou retoma o item selecionado;
- `Ctrl+P` pausa o download atual;
- `Ctrl+F` foca a pesquisa de transferências;
- `Delete` remove o item selecionado da fila;
- `F1` abre a ajuda.

## Ferramentas

A tela **Ferramentas** serve para manutenção do app. Nela dá para:

- conferir as versões do yt-dlp e SpotDL;
- verificar se o FFmpeg está disponível;
- copiar um diagnóstico básico;
- localizar e remover arquivos `.part` e `.ytdl` deixados por downloads interrompidos;
- recarregar a biblioteca;
- abrir a pasta de dados do Epicuro.

A limpeza de arquivos incompletos fica bloqueada enquanto existir download ativo ou pausado.

## Gerar o EXE

Execute:

```text
GERAR_EXE.bat
```

O resultado fica em:

```text
dist\Epicuro\Epicuro.exe
```

O build usa PyInstaller em modo `onedir` e `console=False`. Ao abrir o executável aparece somente o aplicativo. Ao fechar a janela, o processo principal e os processos auxiliares iniciados pelo Epicuro são encerrados.

## Testes

Execute:

```text
TESTAR.bat
```

O script instala as dependências necessárias e roda a suíte com `pytest`. Os testes cobrem persistência, validação de campos, fila, cancelamento, biblioteca, limpeza de arquivos parciais, build sem console e estrutura da interface.

## Estrutura

```text
Epicuro/
├─ epicuro/
│  ├─ core.py
│  ├─ icons.py
│  ├─ platform_utils.py
│  └─ ui.py
├─ assets/
├─ tests/
├─ main.py
├─ requirements.txt
├─ Epicuro.spec
├─ INICIAR_EPICURO.bat
├─ GERAR_EXE.bat
└─ TESTAR.bat
```

As pastas `downloads` e `data` são criadas pelo programa e não precisam ficar no repositório.

## Licença

MIT. O código pode ser usado, modificado e redistribuído livremente nos termos do arquivo [LICENSE](LICENSE).

Use o Epicuro apenas para baixar conteúdo próprio, licenciado ou que você tenha autorização para salvar.
