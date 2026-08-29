# Epicuro 2.0.1

Epicuro é um gerenciador para baixar vídeos, áudios e playlists no Windows. A fila permite iniciar, pausar, cancelar e reorganizar downloads, e os arquivos concluídos ficam disponíveis na biblioteca do aplicativo.

## Recursos

- MP4 e MP3;
- vídeos e playlists;
- links do Spotify com SpotDL;
- escolha de qualidade;
- fila de downloads;
- progresso, velocidade e tempo restante;
- biblioteca com pesquisa e arrastar arquivos para o Explorer ou outros programas;
- pasta de downloads configurável;
- ferramentas de diagnóstico e limpeza de arquivos incompletos;
- executável sem janela de terminal.

## Executar pelo código

Requer Windows 10 ou 11 e Python 3.11 ou mais recente.

1. Extraia a pasta.
2. Abra `INICIAR_EPICURO.bat`.
3. Na primeira execução as dependências são instaladas.
4. Depois disso o aplicativo abre normalmente.

## Gerar a versão portátil

Abra `GERAR_PORTATIL.bat`.

O script cria o executável otimizado, executa um auto-teste e gera:

```text
release\Epicuro-2.0.1-Portable.zip
```

O build usa `PySide6-Essentials` e exclui módulos Qt que o Epicuro não utiliza. O tamanho real é mostrado ao final do processo.

## Dados do aplicativo

As atualizações não dependem mais da pasta onde o programa foi instalado.

```text
Configurações e histórico: %LOCALAPPDATA%\Epicuro
Downloads padrão:         %USERPROFILE%\Downloads\Epicuro
```

## Licença

MIT. Consulte `LICENSE`.

Use o Epicuro somente para conteúdos próprios, licenciados ou que você tenha autorização para baixar.
