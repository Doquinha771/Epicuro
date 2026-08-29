# Epicuro

Epicuro é um gerenciador de downloads para Windows focado em vídeos, áudios e playlists, com fila de transferências, biblioteca local e uma interface simples de usar.

## Recursos

- Download de vídeos em MP4
- Extração de áudio em MP3
- Suporte a vídeos e playlists
- Suporte a links do Spotify com SpotDL
- Escolha de qualidade
- Fila de downloads
- Pausar, retomar, cancelar e reorganizar transferências
- Progresso, velocidade e tempo restante
- Biblioteca com pesquisa
- Arrastar arquivos da biblioteca para o Explorer ou outros programas
- Pasta de downloads configurável
- Ferramentas de diagnóstico e limpeza
- Executável sem janela de terminal

## Executar pelo código

Requer Windows 10 ou 11 e Python 3.11 ou mais recente.

1. Baixe ou clone o projeto.
2. Extraia os arquivos, se necessário.
3. Execute `INICIAR_EPICURO.bat`.
4. Na primeira execução, as dependências serão instaladas automaticamente.

## Gerar o aplicativo

Os scripts incluídos no projeto permitem gerar uma versão portátil ou um instalador para Windows.

Para gerar o executável portátil:

```text
GERAR_PORTATIL.bat
```

Para a versão preparada com instalador, use o projeto de Setup Builder e execute:

```text
GERAR_SETUP.bat
```

## Dados do aplicativo

As configurações e o histórico ficam separados da pasta de instalação:

```text
Configurações e histórico: %LOCALAPPDATA%\Epicuro
Downloads padrão:         %USERPROFILE%\Downloads\Epicuro
```

Isso permite atualizar ou reinstalar o programa sem apagar a biblioteca local.

## Uso e licença

O Epicuro pode ser usado livremente para fins pessoais, educacionais, comerciais, acadêmicos ou de desenvolvimento.

Você pode:

- usar o programa;
- estudar o código;
- modificar;
- criar versões próprias;
- redistribuir;
- incluir em outros projetos;
- publicar;
- usar comercialmente.

As únicas condições são manter o aviso de licença quando redistribuir partes substanciais do código e não usar o projeto de forma intencional para prejudicar os autores ou colaboradores, distribuir malware, cometer fraude, violar a privacidade de terceiros ou apresentar uma versão modificada como se fosse uma versão oficial do Epicuro.

Consulte o arquivo `LICENSE` para os termos completos.

## Aviso

O Epicuro é fornecido sem garantia. Cada pessoa é responsável pelo uso que faz do programa e pelo conteúdo que baixa.

Use serviços e conteúdos de acordo com as permissões, termos aplicáveis e leis da sua região.
