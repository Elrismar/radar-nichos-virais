# Radar de Nichos Virais — MVP gratuito

MVP estático + coletor diário via GitHub Actions + YouTube Data API v3.

## O que faz
- Pesquisa vídeos recentes em várias combinações de tema, idioma e país.
- Encontra canais com poucos inscritos e poucos vídeos, mas com vídeos que têm desempenho desproporcional.
- Guarda snapshots para estimar crescimento diário após a primeira execução.
- Gera `data/results.json`, consumido pelo painel responsivo.
- Executa uma vez por dia no GitHub Actions.

## Custo
O código e GitHub Pages / GitHub Actions em repositório público podem ser usados sem pagamento, sujeitos às regras e limites atuais das plataformas. A YouTube Data API tem cotas gratuitas limitadas. Isto não é um serviço de varredura exaustiva de todo o YouTube.

## Implantação (sem instalar nada no celular)
1. Crie uma conta no GitHub, se ainda não tiver.
2. Crie um repositório **público** chamado `radar-nichos-virais`.
3. Envie todos os arquivos deste ZIP para a raiz do repositório.
4. No Google Cloud Console, crie um projeto, ative **YouTube Data API v3** e crie uma API key.
5. No GitHub, abra `Settings → Secrets and variables → Actions → New repository secret`.
   - Nome: `YOUTUBE_API_KEY`
   - Valor: sua chave da API.
6. Abra `Settings → Pages`, escolha `Deploy from a branch`, branch `main`, pasta `/ (root)`, e salve.
7. Abra `Actions`, habilite workflows se solicitado, e execute `Radar diário` com `Run workflow`.
8. Depois da primeira execução, o painel fica disponível em `https://SEU-USUARIO.github.io/radar-nichos-virais/`.

## Observações de segurança
- A chave fica em GitHub Secrets e nunca é colocada no HTML.
- Não publique a chave em Issues, commits, screenshots ou no arquivo `config.json`.
- Restrinja a API key no Google Cloud à YouTube Data API v3.
- Para um produto público com muitos usuários, reveja políticas, privacidade e quotas antes de ampliar.

## Limites e interpretação
- A cota padrão documentada do YouTube Data API inclui um bucket de 100 chamadas `search.list` por dia e 10.000 unidades/dia para a maioria dos demais métodos; confirme sempre no console porque cotas/políticas podem mudar.
- O workflow faz até 48 buscas por execução, mantendo margem para chamadas adicionais.
- `relevanceLanguage` e `regionCode` ajudam a diversificar resultados, mas não filtram perfeitamente o idioma falado nem representam todos os vídeos de um país.
- A API não revela todos os canais ou todos os dados de crescimento. Views por inscritos é um indicador, não prova de viralidade.
- A primeira execução não conhece crescimento histórico. A velocidade começa a ser estimada depois de snapshots sucessivos.
- O código não usa scraping de páginas do YouTube.
