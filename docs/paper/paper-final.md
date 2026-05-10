---
lang: pt-BR
---

<!-- Capa AGTU formal preservada via build_paper.py (TechGrowth.docx template).
     Não duplicar capa neste markdown — o build script copia o template e
     substitui apenas 5 strings nos paragrafos 3, 4, 12, 13, 16. Body começa
     direto em **Resumo** abaixo. -->

**Resumo**

A frota global Addverb, com mais de trezentos e cinquenta clientes industriais, opera Veículos Guiados Automaticamente (AGV) da família Zippy comandados por voz em noventa e oito idiomas, executando o encadeamento Whisper local, Llama 3 na borda e contingência de nuvem ChatGPT, sobre servidores Supermicro SYS-111E-FWTR com Intel Xeon Scalable. A documentação pública do caso expõe lacuna substantiva em métricas auditáveis de latência, custo e segurança operacional, agravada pela ausência de verificação criptográfica para comandos cuja carga útil pode atingir duas toneladas. Propõe-se a Malha Celular de Inferência sob saturação como arquitetura distribuída que integra seis técnicas revisadas por pares no núcleo — adaptação federada por idioma, redução multiplicativa do *cache* de chave-valor por janela deslizante e atenção entre camadas, decodificação especulativa com chaveamento por entropia, disagregação preenchimento-geração na contingência, isolamento celular por particionamento aleatório e comandos verificáveis sob chaveamento diferenciado por carga útil — somadas a três habilitadores de plataforma: entendimento de linguagem natural executado em rede via comutadores programáveis, agrupamento compartilhado de chave-valor sobre Compute Express Link e roteamento sensível a energia. A composição é demonstrada Pareto-eficiente em cinco eixos — latência de cauda, taxa de contingência, custo, raio de impacto e energia — verificada computacionalmente contra duzentas e cinquenta e seis sub-composições próprias e dominando seis de sete arquiteturas externas modeladas. A validação empírica via simulação Salabim de eventos discretos com semente determinística confirma redução da contingência em fator sete vírgula três e do custo por comando em fator dezenove vírgula sete, ambos com intervalo de confiança de noventa e cinco por cento. A redução do percentil noventa e nove de latência em fator um vírgula um constitui o achado empírico que motiva a Conjectura do Pipeline Saturado, contribuição teórica original que estabelece insensibilidade estrutural do percentil noventa e nove a reduções da taxa de contingência sob saturação da borda e prescreve os três habilitadores de plataforma como caminho operacional. A reprodutibilidade matemática é garantida por cadeia SHA-256 com bit-paridade verificada e auditoria reprodutível disponibilizada em repositório público com identificador persistente Zenodo.

**Palavras-chave:** malha celular de inferência; saturação da borda; isolamento celular; conjectura do pipeline saturado; pareto-eficiência; simulação de eventos discretos.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
**Abstract**

The Addverb global fleet, with more than three hundred and fifty industrial clients, operates Automated Guided Vehicles (AGV) of the Zippy family commanded by voice in ninety-eight languages, running a Whisper local plus Llama 3 edge plus ChatGPT cloud-as-contingency pipeline on Supermicro SYS-111E-FWTR servers with Intel Xeon Scalable. The public documentation of the case reveals a substantial gap in auditable metrics for latency, cost, and operational security, aggravated by the absence of cryptographic verification for commands whose payload may reach two tons. The Cellular Inference Mesh under saturation is proposed as a distributed architecture that integrates six peer-reviewed core techniques — language-federated adaptation, multiplicative key-value cache reduction via sliding window and cross-layer attention, speculative decoding with entropy gating, prefill-decode disaggregation in cloud contingency, cellular isolation by random partitioning, and verifiable commands under payload-differentiated gating — together with three platform enablers: natural language understanding executed in-network via programmable switches, a shared key-value pool over Compute Express Link fabric, and energy-aware routing. The composition is shown Pareto-efficient across five axes — tail latency, cloud-contingency rate, cost, blast radius, and energy — computationally verified against two hundred and fifty-six own sub-compositions and dominating six of seven external architectures modeled from primary numbers. Empirical validation via Salabim discrete-event simulation with deterministic seed confirms cloud-contingency reduction by factor seven point three and cost-per-command reduction by factor nineteen point seven, both at ninety-five per cent confidence interval. The percentile ninety-nine latency reduction by factor one point one constitutes the empirical finding that motivates the Saturated Pipeline Conjecture, the original theoretical contribution that establishes the structural insensitivity of percentile ninety-nine to cloud-contingency rate reductions under edge saturation and prescribes the three platform enablers as operational path. Mathematical reproducibility is guaranteed by SHA-256 hash chain with verified bit-parity and reproducible auditing made available in a public repository of the author.

**Keywords:** cellular inference mesh; edge saturation; cellular isolation; saturated pipeline conjecture; pareto-efficiency; discrete-event simulation.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
## 1. Introdução

A operação industrial contemporânea encontrou na voz uma interface natural para guiar veículos autônomos no chão de fábrica. Comandos falados em dezenas de idiomas, transmitidos em poucos segundos, devem retornar ações executáveis em frações de segundo — sob risco de impacto físico se mal interpretados. Esta convergência entre linguagem natural e sistemas ciberfísicos no segmento industrial redefine o padrão de qualidade exigido da inferência de modelos de linguagem em produção, deslocando o foco da média para a cauda da distribuição de latência. O desafio operacional central deste segmento é simultaneamente técnico, financeiro e de segurança: sustentar latência sub-segundo para comandos críticos, conter custo unitário de inferência sob volume crescente da indústria 4.0, e impor verificação criptográfica diferenciada quando a carga útil do veículo configura risco físico mensurável.

A literatura de sistemas distribuídos formaliza essa exigência por meio de dois resultados clássicos. O primeiro é o teorema PACELC, proposto por Abadi (2012, p. 38), que decompõe o compromisso fundamental dos sistemas distribuídos em duas decisões sequenciais: durante uma partição de rede há de escolher entre disponibilidade e consistência; em operação normal há de escolher entre latência e consistência. O segundo é o fenômeno *Tail at Scale*, descrito por Dean e Barroso (2013), que demonstra como a latência da cauda — percentis 99 e 99,9 — torna-se a métrica honesta em sistemas com leque cooperativo de requisições, decorrente da inevitabilidade da composição de variabilidades entre componentes.

No domínio específico da inferência em produção de Grandes Modelos de Linguagem (LLM), esses dois resultados ganham agudez particular. A inferência autorregressiva exige acesso constante ao *cache* de chave-valor mantido em memória de alta largura de banda, e qualquer queda à nuvem por insuficiência local incorre em propagação em redes de longa distância que infla o percentil 99 muito acima do que sugerem ensaios de referência isolados de FLOPs (Kwon et al., 2023). Decisões arquiteturais que parecem otimizações marginais — gerência do *cache*, disagregação das fases de preenchimento e geração, decodificação especulativa, isolamento celular — passam a discriminar até quatro ordens de grandeza em capacidade sustentada (Patel et al., 2024; Qin et al., 2025).

O caso Addverb, documentado em ZenML (2025) e em material institucional Addverb (2024), exemplifica a ponta industrial deste dilema: frota global de mais de trezentos e cinquenta clientes — Coca-Cola, Amazon, DHL e similares em quinze ou mais países — opera Veículos Guiados Automaticamente (AGV) da família Zippy comandados por voz em noventa e oito idiomas via encadeamento Whisper local, Llama 3 na borda e contingência de nuvem ChatGPT, executado sobre servidores Supermicro de borda de alta capacidade.[^hw] Notavelmente, a documentação oficial ZenML reconhece que o material original possui caráter estritamente mercadológico, sem apresentação de métricas específicas de latência, custo ou taxa de erro,[^marketing] e admite a ausência de discussões sobre as implicações de segurança de equipamento industrial controlado por voz[^safety] — fenda que justifica intervenção quantitativa em vez de descrição puramente narrativa.

Esta investigação propõe a Malha Celular de Inferência sob saturação, arquitetura distribuída que articula três blocos complementares. O primeiro reduz o consumo de memória local pela combinação de adaptação federada por idioma com a redução multiplicativa do *cache* de chave-valor. O segundo acelera o caminho serial de inferência pela decodificação especulativa e pela disagregação das fases de geração no recurso de nuvem. O terceiro contém o raio de impacto operacional pelo particionamento aleatório dos domínios servidos, somado à verificação criptográfica diferenciada por carga útil dos comandos. Três habilitadores de plataforma — entendimento de linguagem natural executado dentro da rede, agrupamento compartilhado de *cache* entre células cooperativas e roteamento sensível a energia — completam a composição. As nove técnicas individuais provêm da literatura revisada por pares de mais alto impacto e estão detalhadas na Seção 2.1; a contribuição autoral reside na composição multiplicativa Pareto-eficiente verificada computacionalmente e na Conjectura do Pipeline Saturado articulada na Seção 2.3.

O trabalho organiza-se em três seções principais. A Seção 2.1 apresenta os artigos selecionados que sustentam a fundamentação teórica das nove técnicas integradas. A Seção 2.2 conduz a análise técnica e arquitetural cobrindo os nove itens obrigatórios. A Seção 2.3 discute os compromissos nominais aplicáveis e apresenta os resultados quantitativos validados empiricamente sobre trezentas réplicas Monte-Carlo, articulando a Conjectura do Pipeline Saturado e a verificação computacional da Pareto-eficiência. A Seção 3 sintetiza as considerações finais com direções concretas de continuidade. Os Apêndices A e B detalham, respectivamente, o esboço da prova do Theorem (Lemmas 1–3) e a fundamentação matemática da Conjectura.

[^hw]: Servidores Supermicro IoT SuperServer SYS-111E-FWTR equipados com processadores Intel Xeon Scalable de 5ª/4ª Geração de até trinta e dois núcleos e até dois terabytes de memória RAM DDR5; especificações detalhadas na Seção 2.2.4.

[^marketing]: No original: *"clearly marketing content … no specific metrics provided"* (ZenML, 2025).

[^safety]: No original: *"the safety implications of voice-controlled industrial equipment are not discussed"* (ZenML, 2025).

## 2. Desenvolvimento

### 2.1. Artigos Selecionados e Fundamentação Teórica

A fundamentação teórica da arquitetura proposta estrutura-se em três eixos complementares de literatura revisada por pares publicada entre 2022 e 2026, cada um mapeado a uma camada arquitetural específica e alinhado a um caso-espelho industrial documentado no banco ZenML LLMOps Database (ZenML, 2025). A seleção priorizou fontes em conferências de alto impacto em sistemas de inferência (ICML, NeurIPS, MLSys, OSDI, ISCA, FAST, NSDI, SOSP, ASPLOS, EMNLP), normas técnicas (NIST SP, IEC) e referências de fronteira da indústria (AWS Builders' Library, IEEE Communications Surveys & Tutorials). Os três eixos descritos a seguir consolidam, respectivamente, a adaptação e redução de memória; a decodificação especulativa e a disagregação das fases de geração; e o isolamento celular somado aos habilitadores de plataforma.

#### Eixo 1 — Adaptação multilíngue e redução do cache de chave-valor

A inferência em produção de adaptadores multi-LoRA (*Low-Rank Adaptation*, adaptação por matrizes de baixo posto) com redução agressiva do *cache* de chave-valor na borda apoia-se em duas linhagens convergentes. A primeira parte de Hu et al. (2022), que introduzem na ICLR a decomposição de baixo posto e reduzem parâmetros treináveis em até quatro ordens de grandeza sem degradação significativa de qualidade; é estendida por Dettmers et al. (2023), que compõem na NeurIPS o QLoRA via quantização NF4 informação-teoricamente ótima combinada com quantização dupla, viabilizando ajuste fino de modelos de sessenta e cinco bilhões de parâmetros em uma única unidade gráfica de quarenta e oito gigabytes; e é consolidada por Sheng et al. (2024), que apresentam na MLSys o S-LoRA com paginação unificada, colocando pesos de adaptador e *cache* no mesmo alocador paginado e habilitando milhares de adaptadores concorrentes em processamento heterogêneo em lote.

A segunda linhagem trata da redução do próprio *cache* de chave-valor: Kwon et al. (2023) introduzem na SOSP a *PagedAttention* com paginação inspirada em memória virtual; Shazeer (2019) propõe a *Multi-Query Attention* (MQA, projeção única compartilhada de chave-valor); Ainslie et al. (2023) generalizam na EMNLP para *Grouped-Query Attention* (GQA, chave-valor agrupados); DeepSeek-AI (2024) consolida a *Multi-Head Latent Attention* (MLA, compressão latente do *cache* por projeção de baixa dimensão) em DeepSeek-V3; Brandon et al. (2024) propõem a *Cross-Layer Attention* (CLA, *cache* compartilhado entre camadas); e Beltagy, Peters e Cohan (2020) formalizam a atenção em janela deslizante em Longformer. Os casos-espelho industriais Convirza/Predibase (LoRAX, documentado em ZenML, 2025) e Character.AI Kaiju materializam o paradigma com sessenta adaptadores Llama-3-8B em produção, MQA combinada com janela deslizante de oito mil *tokens*, *cache* compartilhado entre camadas e quantização INT8 — embora a afirmação corporativa Character.AI de vinte mil consultas por segundo abaixo de um centavo por hora seja tratada aqui como evidência qualitativa por carecer de fonte revisada por pares de mais alto impacto.

#### Eixo 2 — Decodificação especulativa e disagregação das fases preenchimento-geração

A aceleração do caminho serial de inferência sob contingência de nuvem apoia-se em duas frentes coordenadas. Quanto à disagregação das fases preenchimento e geração, Patel et al. (2024) demonstram na ISCA com Splitwise que separar a fase de preenchimento (limitada por cômputo) da fase de geração (limitada por memória) em agrupamentos heterogêneos rende ganho de 1,4 vezes em vazão a vinte por cento menor custo, ou alternativamente 2,35 vezes em vazão sob o mesmo orçamento de potência; Zhong et al. (2024) refinam na OSDI com DistServe atingindo 7,4 vezes em vazão útil; Agrawal et al. (2024) propõem preenchimentos fragmentados em Sarathi-Serve com 5,6 vezes de ganho em capacidade; Qin et al. (2025) consolidam Mooncake — laureado como *Best Paper* na FAST 2025 — com agrupamento global centrado em *cache* de chave-valor; e Yu et al. (2022) introduzem o lote contínuo dinâmico em Orca na OSDI.

Quanto à decodificação especulativa propriamente dita, Leviathan, Kalman e Matias (2023) formalizam na ICML 2023 Oral a fórmula canônica do fator de aceleração esperado, apresentada na Equação (1):

$$
\mathrm{Speedup}(\alpha, \gamma, c) = \frac{1 - \alpha^{\gamma+1}}{(1-\alpha)(\gamma c + 1)} \quad (1)
$$

Nesta relação, $\alpha$ representa a taxa de aceitação por *token* do modelo rascunhador, $\gamma$ representa o número de *tokens* propostos por chamada e $c$ representa o custo relativo do rascunhador frente ao modelo verificador. Para a parametrização realista com $\alpha = 0{,}9$, $\gamma = 8$ e $c = 0{,}05$, o cálculo direto rende fator 4,38 — valor que substitui a estimativa otimista de 6,5 vezes válida apenas no limite teórico $c \to 0$. Chen et al. (2023) apresentam variante DeepMind concorrente, Cai et al. (2024) propõem o Medusa com múltiplas cabeças de geração simultâneas, e Li et al. (2025) atingem fator de aceleração de até 6,5 vezes com EAGLE-3 via *Training-Time Test*, abordagem adotada *de facto* em SGLang, TensorRT-LLM e vLLM v1. As curvas de fator de aceleração para as parametrizações realistas estão sintetizadas na Figura 1.

A análise técnica conduzida nas seções seguintes apoia-se nestas curvas para fundamentar a escolha do par $(\gamma, c)$ adotado na arquitetura proposta. A Figura 1 apresenta as parametrizações canônicas $\alpha = 0{,}9$, $\gamma \in \{2, 4, 8\}$ e $c \in \{0{,}05;\,0{,}10;\,0{,}20\}$.

![](figures/figura-01-speculative-speedup.png)

*Figura 1 — Curvas do fator de aceleração da decodificação especulativa segundo Leviathan, Kalman e Matias (2023); marcadores destacam as parametrizações canônicas de 1,98 e 4,38 vezes.*

#### Eixo 3 — Isolamento celular, Mobile Edge Intelligence e habilitadores de plataforma

O terceiro eixo consolida o isolamento celular, a moldura *Mobile Edge Intelligence* e os três habilitadores de plataforma. MacCárthaigh (2019), na AWS Builders' Library, sustenta que a distribuição de trabalhadores em subconjuntos pseudoaleatórios reduz combinatoriamente o raio de impacto de falhas correlacionadas; Dean e Barroso (2013) caracterizam o fenômeno *Tail at Scale* com soluções via requisições redundantes especulativas e requisições atadas; Qu et al. (2024) consolidam em IEEE Communications Surveys & Tutorials a taxonomia *Mobile Edge Intelligence* para LLMs cobrindo armazenamento de *cache* na borda, treino na borda e inferência na borda.

Para os três habilitadores de plataforma, três frentes complementam a composição. Quanto ao entendimento de linguagem natural executado em rede, Gao et al. (2024) introduzem na NSDI o sistema Sirius compondo cadeias de funções de rede em comutadores compatíveis com P4 com latência submicrossegundo por estágio de consulta-ação, possibilitando descarregamento de detecção de palavra-de-ativação e identificação de idioma antes do LLM da borda. Quanto ao agrupamento compartilhado de *cache* sobre Compute Express Link, Tang et al. (2024) demonstram no NeurIPS ML4Sys que armazenar *cache* em memória CXL atinge desempenho de transferência comparável à interconexão CPU-GPU, viabilizando aumento de trinta por cento no tamanho do lote sob mesmo objetivo de latência e até 7,5 vezes maior utilização de GPU para preenchimento, com Yang et al. (2026) sistematizando o resultado no sistema Beluga publicado em ACM SIGMOD e Li et al. (2023) consolidando na ASPLOS o sistema Pond com paginação por agrupamento de memória de plataforma de nuvem. Quanto ao roteamento sensível a energia, Niu et al. (2025) introduzem a moldura TokenPowerBench para aferição de consumo energético em inferência LLM com normalização em *joules* por *token*, e Wilhelm, Wittkopp e Kao (2025) advogam na EuroMLSys a métrica de energia por *token* como padrão de comparação. O posicionamento Pareto-eficiente da composição completa em cinco eixos — percentil 99, contingência, custo, raio de impacto e energia — estende a moldura de Recasens et al. (2024) para inferência de Modelos de Linguagem Pequenos, originalmente bidimensional em vazão-latência, ao domínio borda-nuvem industrial multi-AGV.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
### 2.2. Análise Técnica e Arquitetural

A análise técnica do caso Addverb percorre, da camada de aplicação até a camada de plataforma, as decisões de engenharia que sustentam a operação industrial: começa pelo desafio funcional que motivou a adoção de modelos de linguagem na frota; passa pela escolha do modelo e pelos tipos de dados manipulados; examina as garantias de privacidade exigidas; descreve a infraestrutura de servidores de borda com sua composição de memória e atenção; quantifica o impacto de latência sobre comandos de voz em dezenas de idiomas; e fecha com as decisões de segurança e arquitetura que diferenciam o chaveamento por carga útil para comandos de massa crítica. A organização das seis sub-seções a seguir mapeia esses temas aos nove itens obrigatórios da decomposição metodológica adotada, com fundamentação direta na literatura revisada por pares e elaboração própria justificada onde a fonte original não publica detalhes.

#### 2.2.1. Desafio e objetivos

A frota global Addverb opera Veículos Guiados Automaticamente (AGV) em mais de 350 clientes industriais — Coca-Cola, Amazon, DHL e similares em 15+ países —, gerando aproximadamente 25.000 sortimentos por hora por instalação tipo (Addverb, 2024; ZenML, 2025) e processando comandos de voz de duração 5–30 s em 98 idiomas via composição Whisper Large-v3 (1,55 bilhões de parâmetros), Llama 3 8B INT4 e contingência de nuvem ChatGPT. O desafio operacional central é dúplice: reduzir tempo de manutenção (anteriormente exigia deslocamento de engenheiros, com horas de parada por incidente) e superar a barreira linguística entre operadores de chão de fábrica em noventa e oito idiomas. Os objetivos coordenados são (i) auto-resolução por equipes não treinadas via comando de voz natural, (ii) baixa latência local em proximidade da operação, (iii) redução de dependência de conectividade de rede de longa distância, (iv) controle de custo de *tokens* evitando interfaces de programação de aplicação de nuvem em consultas triviais e (v) escalabilidade para frotas crescentes.

#### 2.2.2. Tamanho do modelo e tipo de dados

A versão exata do Llama 3 implantado na borda não é declarada nas três fontes triangulares; a inferência justificada pela pegada operacional CPU-only Xeon Granite Rapids aponta para Llama 3 8B INT4 quantizado via AWQ, GPTQ ou NF4 estilo QLoRA (Dettmers et al., 2023), permitindo execução em menos de 16 GB ativos com paralelismo tensorial igual a um. Whisper Large-v3 (1,55 bilhão de parâmetros) opera o reconhecimento automático de fala localmente. O ChatGPT na contingência de nuvem opera modelo não declarado, consistente com gpt-4o ou gpt-4o-mini. O tipo de dados manipulado abrange áudio multilíngue de curta duração (cinco a trinta segundos), texto transcrito multilíngue, comandos estruturados em linguagem específica de domínio sobre JSON Zippy, telemetria operacional do AGV e registros de auditoria.

#### 2.2.3. Privacidade

A motivação da borda no caso Addverb é precisamente a redução de exposição: áudio dos operários (taxa de captura típica 16 kHz, ~32 kB/s, com identificação biométrica vocal teoricamente possível com amostras curtas de áudio) é processado localmente pelo Whisper em latência mediana de aproximadamente 200 ms para 5–10 s de áudio, com apenas a transcrição textual (~50–300 *tokens*, ≤ 1 kB) transitando à contingência ChatGPT (taxa observada $p_{fb} \approx 4{,}1\%$ pós-arquitetura proposta; cf. Tabela 2) quando acionada. Esta arquitetura, contudo, deixa duas lacunas críticas não tratadas publicamente: ausência de mascaramento de informações pessoais identificáveis pré-nuvem no caminho de contingência (risco de vazamento de nomes próprios e identificadores) e ausência de Computação Confidencial local. A recomendação canônica adota TLS 1.3 no canal de subida (Rescorla, 2018), mascaramento automático de informações pessoais identificáveis pré-contingência, Intel Trust Domain Extensions (TDX, isolamento criptográfico de hardware) e arquitetura *Zero Trust* formalizada em Rose et al. (2020) na NIST Special Publication 800-207. Decisões de armazenamento e replicação distribuída — como tratamento do agrupamento compartilhado de chave-valor e estratégia de quórum de escrita sob partição — seguem o registro canônico de compromissos sistêmicos em Kleppmann (2017).

#### 2.2.4. Infraestrutura

A escolha da infraestrutura de borda condiciona o que é possível executar localmente sem queda à nuvem. O servidor adotado pela Addverb privilegia formato compacto, ampla capacidade de memória e largura de banda para sustentar a inferência local concorrente, mas opera apenas em CPU (sem aceleração por unidade gráfica dedicada), o que torna o orçamento de memória e a taxa de transferência DDR5 os fatores críticos para o desempenho do preenchimento e da geração de *tokens*. O Supermicro IoT SuperServer SYS-111E-FWTR — confirmado *verbatim* nas três fontes triangulares (Intel Corporation, 2024; Addverb, 2024; ZenML, 2025) — opera em formato 1U de profundidade reduzida com Single Socket E (LGA-4677), Intel Xeon Scalable de 5ª/4ª Geração de até trinta e dois núcleos e sessenta e quatro fluxos de execução, oito módulos DIMM DDR5-4800/5600 RDIMM até dois terabytes, dois SATA 2,5 polegadas mais um M.2 NVMe, duas portas 10GbE RJ45 mais uma 1GbE BMC, três PCIe 5.0 x16 (um *Low-Profile* e dois *Full-Height Full-Length*), seis ventiladores e duas fontes 800 W Titanium, com Intel AVX-512 e DL Boost ativados.

A composição multiplicativa de técnicas de redução do *cache* de chave-valor, sintetizada na Tabela 1, deriva-se do modelo dimensional canônico da atenção *Multi-Head Attention* formalizado por Vaswani et al. (2017), apresentado na Equação (2):

$$
M_{MHA} = N_{\text{layers}} \times N_{\text{heads}} \times 2 \times d_{\text{head}} \times s \times b \quad (2)
$$

Nesta relação, as variáveis representam: $N_{\text{layers}}$, o número de camadas *Transformer* (trinta e duas para Llama 3 8B); $N_{\text{heads}}$, o número de cabeças de atenção (trinta e duas); $d_{\text{head}}$, a dimensão por cabeça (cento e vinte e oito); $s$, o comprimento da sequência (duzentos e cinquenta e seis *tokens*); e $b$, o número de *bytes* por elemento (dois em BF16). Substituindo os valores nominais, $M_{MHA} \approx 134{,}2$ MB para duzentos e cinquenta e seis *tokens*, viabilizando concorrência de mais de sessenta e quatro comandos em voo na borda sem paginação para disco sob a configuração final adotada.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
*Tabela 1 — Decomposição multiplicativa do cache de chave-valor em Llama 3 8B (cenário Addverb com comandos AGV de aproximadamente 256 tokens, BF16); fatores de redução invariantes ao comprimento da sequência enquanto a configuração de atenção permanecer fixa.*

| **Técnica** | **Estratégia central** | **KV (256 tok, BF16)** | **Redução vs MHA** | **Paper âncora** |
|---|---|---|---|---|
| MHA (baseline) | 32 camadas × 32 heads × 2 (K+V) × 128 dim × 256 tok × 2 B | 128 MiB ≡ 134,2 MB | 1,0× | Vaswani et al. (2017) |
| MQA | Única projeção K/V compartilhada entre heads | 4,0 MB | 32× | Shazeer (2019) |
| GQA-8 | 8 grupos K/V | 32 MB | 4× | Ainslie et al. (2023) |
| Janela deslizante 128 | Janela truncada a 128 tokens (50% do contexto) | 64 MB | 2× | Beltagy et al. (2020) |
| MLA (DeepSeek-V3) | Compressão latente $d_c=512$ | ~13 MB | ~10× | DeepSeek-AI (2024) |
| MLA + janela 128 | Composto multiplicativo | ~6 MB | ~19× | Composição autoral |
| MLA + janela 128 + CLA-2 | + 2 grupos cross-layer | ~3,4 MB | ~38× | Brandon et al. (2024) |

*Nota.* Os fatores de redução são invariantes ao comprimento da sequência enquanto a configuração de atenção permanecer fixa. Para uma sequência de 8.192 *tokens* (janela de contexto máxima do Llama 3 8B), a célula MHA atinge aproximadamente quatro gigabytes com fatores multiplicativos idênticos nas técnicas subsequentes. A composição final MLA mais janela deslizante de 128 *tokens* mais CLA-2 é a adotada no núcleo da arquitetura proposta.

#### 2.2.5. Impacto de latência

As fontes Addverb públicas não publicam métricas de Tempo até o Primeiro Token (TTFT), Tempo por Token de Saída (TPOT), latência p50, p95 ou p99, fato reconhecido literalmente pela documentação ZenML como material estritamente mercadológico sem métricas específicas. A estimativa inicial calibrou-se por aproximações de fronteira: ensaios de referência Intel para Llama 3 8B em BF16 sobre AWS m7i.metal-48xl indicam aproximadamente 50–100 ms por *token*, e Granite Rapids alcança menos de 100 ms por *token* em Llama 3 70B sob a mesma microarquitetura, projetando 80–150 *tokens* por segundo de vazão em Llama 3 8B INT4 e resposta de comandos típicos com até cinquenta *tokens* em menos de quinhentos milissegundos na borda.

A concorrência admissível na borda é dimensionada pela Lei de Little (Little, 1961), apresentada na Equação (3):

$$
L = \lambda \cdot W \quad (3)
$$

Nesta relação, $L$ representa o número médio de comandos em voo no sistema, $\lambda$ representa a taxa de chegada de comandos e $W$ representa o tempo médio de permanência por comando, conforme tratamentos clássicos em Glasserman (2003) e Asmussen e Glynn (2007). Aplicando-se a relação com $\lambda = 2{,}0$ eventos por segundo por veículo em frota de dez AGVs cooperativos e tempo médio agregado estimado $W = 250$ ms, o número médio de comandos em voo previa-se em $L \approx 5{,}0$. A simulação Salabim de eventos discretos, sintetizada na Tabela 2 da Seção 2.3, mediu $L_{\text{obs}} \approx 25{,}8$ comandos em voo com $\lambda \approx 20$ eventos por segundo e $W_{\text{obs}} \approx 1{,}29$ s. A Lei de Little permanece exata (erro inferior a 1%), mas a calibração inicial subestimou $W$ em fator de aproximadamente cinco vezes, decorrente da composição serial de Whisper, preenchimento e geração de cinquenta *tokens* dominar a latência operacional.

A análise *Roofline* da arquitetura, apresentada na Figura 2, confirma que a operação típica do preenchimento em comandos AGV de duzentos e cinquenta e seis *tokens* — intensidade aritmética próxima de dois FLOP por *byte* — recai claramente no regime limitado por memória sobre Intel Xeon Granite Rapids com DDR5-5600 octa-canal (358 GB/s agregados; pico aritmético AVX-512 INT4 aproximado de 2.150 GFLOPs/s). Justifica-se assim a busca por redução agressiva do *cache* de chave-valor antes de qualquer otimização de cômputo, em consonância com a decomposição preenchimento-geração reportada em Patel et al. (2024) com ganho de 2,35 vezes sob mesmo orçamento de potência.

![](figures/figura-02-roofline.png)

*Figura 2 — Análise Roofline de Llama 3 8B INT4 sobre Intel Xeon Granite Rapids com DDR5-5600.*

#### 2.2.6. Segurança e arquitetura técnica

A arquitetura híbrida borda-nuvem do Addverb público opera em três camadas — camada AGV, camada borda sobre Supermicro SYS-111E-FWTR e camada nuvem sobre ChatGPT — sem *cache* de chave-valor compartilhado, sem multi-LoRA, sem decodificação especulativa e sem verificação criptográfica de comandos. Este último ponto configura risco crítico, dado que o Zippy Tug, com capacidade de carga de duas toneladas, é dirigido por comando de processamento de linguagem natural cujo erro pode causar dano físico mensurável.

A arquitetura proposta integra seis camadas técnicas do núcleo complementadas por três habilitadores de plataforma. A primeira camada implementa multi-LoRA federado por idioma com paginação unificada via S-LoRA (Sheng et al., 2024) e ajuste fino federado via OpenFedLLM (Ye et al., 2024), eliminando a barreira linguística sem custo proibitivo de modelos dedicados. A segunda aplica redução multiplicativa do *cache* por MLA combinada com janela deslizante e CLA, atingindo redução combinatória de aproximadamente trinta e oito vezes conforme decomposição da Tabela 1. A terceira camada introduz decodificação especulativa em redes de longa distância com EAGLE-3 (Li et al., 2025) e chaveamento por entropia sobre a fórmula canônica de Leviathan, Kalman e Matias (2023), com fator de aceleração esperado de aproximadamente quatro vezes em parametrização realista. A quarta camada aplica disagregação preenchimento-geração na contingência de nuvem via Mooncake (Qin et al., 2025) sobre Splitwise (Patel et al., 2024) sobre Sarathi-Serve (Agrawal et al., 2024). A quinta camada implementa isolamento celular com particionamento aleatório sob configuração $M=8$ e $k=2$, resultando em raio de impacto combinatorial de aproximadamente 3,57% (MacCárthaigh, 2019), formalizado na Equação (4):

$$
\mathrm{BlastRadius}(M, k) = \frac{1}{\binom{M}{k}} \quad (4)
$$

Nesta relação, $M$ representa o número total de trabalhadores na célula e $k$ representa o número de trabalhadores por subconjunto pseudoaleatório. A sexta camada introduz comandos verificáveis com chaveamento diferenciado por carga útil: o Zippy 6, com seis quilos, opera em modo PA/EL com auto-aprovação local, enquanto o Zippy Tug, cuja carga útil pode atingir duas toneladas, requer atestação criptográfica Intel TDX em quórum dois de três sob modo PC/EC, materializando o compromisso PACELC (Abadi, 2012) sob política operacional concreta alinhada à norma IEC 61508 (IEC, 2010) de Segurança Funcional para sistemas eletrônicos críticos (cf. Figura 3).

Os três habilitadores de plataforma complementam o núcleo: o entendimento de linguagem natural executado dentro da rede sobre P4 (Gao et al., 2024) descarrega detecção de palavra-de-ativação e identificação de idioma para comutadores em *line rate*; o agrupamento compartilhado de chave-valor sobre Compute Express Link 3.0 (Yang et al., 2026; Tang et al., 2024) compartilha *cache* entre AGVs cooperativos da mesma célula; e o roteamento sensível a energia (Niu et al., 2025; Wilhelm et al., 2025) minimiza *joules* por comando via redistribuição inteligente entre instâncias.

![](figures/figura-03-decision-tree.png)

*Figura 3 — Árvore de decisão do chaveamento por carga útil sob "Zero Trust" operacionalizando o compromisso PACELC.*

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
### 2.3. Discussão

A análise técnica conduzida na Seção 2.2 expõe a tensão central entre latência inferencial sub-segundo, custo operacional contido e segurança operacional sob carga útil diferenciada — tensão sistematicamente caracterizada por Mitzenmacher e Shahout (2025) em *Stochastic Systems*. A discussão a seguir destila os compromissos nominais aplicáveis, apresenta os resultados quantitativos validados empiricamente, articula a Conjectura do Pipeline Saturado, verifica computacionalmente a Pareto-eficiência da arquitetura proposta e registra as principais limitações.

#### 2.3.1. Compromissos nominais

Antes de examinar os resultados empíricos, cumpre enumerar os seis compromissos com nome próprio que sustentam a análise técnica e arquitetural. Cada um deles é um resultado clássico da literatura de sistemas distribuídos, cuja aplicação à inferência em produção de Grandes Modelos de Linguagem em encadeamento industrial multilíngue conforma decisões operacionais concretas na arquitetura proposta.

O teorema PACELC (Abadi, 2012) decompõe sequencialmente o compromisso em dois regimes: disponibilidade *versus* consistência durante partição e latência *versus* consistência em modo normal. Esta formulação é operacionalizada na proposta como chaveamento diferenciado por carga útil — o Zippy 6 opera em PA/EL com auto-aprovação local, enquanto o Zippy Tug opera em PC/EC com atestação criptográfica em quórum dois de três.

O fenômeno *Tail at Scale* (Dean & Barroso, 2013) estabelece os percentis 99 e 99,9 como métricas honestas em sistemas distribuídos com leque cooperativo, justificando o emprego de requisições redundantes especulativas e requisições atadas na malha AGV. A Lei de Little, formalizada na Equação (3), foi calibrada e validada empiricamente conforme registrado na Seção 2.2.5; a divergência entre $W_{\text{est}}$ e $W_{\text{obs}}$ é o achado que motiva a Conjectura do Pipeline Saturado discutida na Seção 2.3.3.

A análise Pollaczek-Khinchine para fila M/G/1 com tempo de serviço log-normal demonstra que a variância do tempo de serviço infla diretamente o percentil 99 — análise específica para inferência em produção de LLM com tamanho de *token* variável é desenvolvida por Yang, Xu e Jiao (2024). A análise *Roofline*, apresentada na Figura 2, impõe teto sustentado de aproximadamente 720 GFLOPs/s limitado por memória ao Llama 3 8B INT4 sobre DDR5-5600 — patamar que justifica a busca por redução agressiva do *cache* de chave-valor antes de otimização de cômputo. O particionamento aleatório de domínios de MacCárthaigh (2019), formalizado na Equação (4), fundamenta operacionalmente o isolamento celular adotado.

O posicionamento Pareto-eficiente da composição completa estende a moldura de Recasens et al. (2024) a cinco eixos, e os métodos para gerência paginada de *cache* em agrupamentos CXL são introduzidos por Li et al. (2023) no sistema Pond, sustentando o habilitador de plataforma da proposta.

#### 2.3.2. Resultados empíricos

A simulação Salabim de eventos discretos, conduzida com semente determinística $\mathtt{seed} = 42$ sobre trezentas réplicas Monte-Carlo distribuídas em três cenários de operação e amostradas sobre faixa paramétrica realística — taxa de chegada $\lambda \in [1{,}95;\,2{,}05]$ eventos por segundo por AGV; partição no canal de subida em $[1{,}5\%;\,2{,}5\%]$; oscilação multiplicativa no tempo de ida-e-volta do canal de subida em $[0{,}9;\,1{,}1]$ — produziu os resultados sintetizados na Tabela 2. Os intervalos de confiança de 95% foram calculados sobre as réplicas conforme metodologia padrão de simulação estocástica documentada por Glasserman (2003) e Asmussen e Glynn (2007). A reprodutibilidade matemática é garantida por cadeia SHA-256 sobre os arquivos-fonte e os artefatos de saída, e a re-execução com a mesma semente produz arquivos bit-idênticos — propriedade auditada pelo teste `test_reproducibility` no repositório público do autor (Flores, 2026); o caderno computacional `colab/replication.ipynb` permite que terceiros reproduzam os mesmos *hashes* em ambiente Google Colab sem configuração local.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
*Tabela 2 — Resultados empíricos validados (n = 300 réplicas Monte-Carlo sobre faixa paramétrica realística; intervalo de confiança de 95%; semente = 42).*

| **Métrica** | **Linha de base (Addverb público)** | **Proposta (Malha Celular)** | **Fator real** | **Projeção analítica (Apêndice A)** |
|---|---|---|---|---|
| p99 de latência (cenário nominal) | 1.740 ± 0,5 ms | 1.576 ± 0,6 ms | 1,1× | Theorem prediz 4,77×; gap explicado pela Conjectura do Pipeline Saturado (Apêndice B) |
| Taxa de contingência à nuvem | 30,02% ± 0,03% | 4,10% ± 0,02% | 7,3× | Theorem prediz 13,3× analítico; empírico mais conservador devido a sobrecarga de chaveamento |
| Custo por comando | US\$~0,0809 ± 0,0002 | US\$~0,00410 ± 1·10⁻⁵ | 19,7× | Theorem prediz 31,0× analítico; empírico contém sobrecarga aditiva de borda |
| Lei de Little ($L = \lambda W$) | erro $<10^{-9}$ | erro $<10^{-9}$ | — | erro $< 5\%$ (empiricamente validada) |

*Nota.* Resultados de simulação Salabim de eventos discretos com semente determinística (`seed_canonical = 42`), trezentas réplicas Monte-Carlo por cenário, duração de 1.800 segundos simulados por réplica. Cada réplica $i$ amostra parâmetros uniformes da faixa operacional com `random.Random(42 + i)` em isolamento (sem estado global), garantindo reprodutibilidade absoluta. Intervalos de confiança de 95% calculados sobre as réplicas. A reprodutibilidade matemática é garantida por cadeia SHA-256 sobre os arquivos-fonte e os artefatos de saída; a re-execução com a mesma semente produz *hashes* bit-idênticos, propriedade auditada pelo teste `test_reproducibility` no repositório público do autor (Flores, 2026). O contraste entre o fator analítico de 4,77× projetado pelo Theorem para o percentil 99 e o fator empírico de 1,1× efetivamente medido **não constitui inconsistência da arquitetura proposta**: é o achado central que motiva e valida localmente a Conjectura do Pipeline Saturado, formalizada na Seção 2.3.3 e demonstrada matematicamente no Apêndice B sob a hipótese de saturação $L_{\text{edge}} \approx L_{\text{cloud}}$ empiricamente observada.

A Tabela 3 decompõe analiticamente a contribuição estimada de cada técnica para os ganhos observados. As estimativas são derivadas das fórmulas canônicas dos artigos-âncora, não medidas empiricamente via execuções de ablação sistemáticas — uma ablação empírica completa constitui direção futura discutida na Seção 3.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
*Tabela 3 — Ablação analítica por técnica: contribuição estimada de cada componente para os ganhos observados.*

| **Componente removido** | **Métrica afetada** | **Contribuição estimada** | **Fórmula-âncora** |
|---|---|---|---|
| Multi-LoRA federado por idioma | Taxa de contingência | −3,0× (contingência ~12% sem LoRA) | S-LoRA paginação unificada (Sheng et al., 2024) |
| Cache MLA + janela + CLA-2 | Concorrência local | −38× (volta a 134 MB MHA) | DeepSeek-V3 (2024) + Brandon et al. (2024) |
| Decodificação especulativa | *Tokens* cloud por invocação | −4,38× (sem amostragem por rejeição) | Leviathan, Kalman & Matias (2023) |
| Disagregação preenchimento-geração | p99 da contingência | −2,35× (Splitwise off) | Patel et al. (2024) ISCA |
| Isolamento celular + particionamento | Raio de impacto | 25% → 3,57% (sem particionamento aleatório, fator 7×) | MacCárthaigh (2019) AWS |
| Comandos verificáveis | Segurança operacional | restrição rígida (binária; chaveamento obrigatório) | Rose et al. (2020) NIST 800-207 |

*Nota.* As contribuições por técnica são estimativas analíticas derivadas das fórmulas canônicas dos artigos-âncora, não medidas empiricamente via execuções de ablação sistemáticas. Uma ablação empírica completa (seis componentes × trezentas réplicas × 1.800 segundos simulados) constitui direção futura discutida na Seção 3. A coluna *Métrica afetada* indica o eixo principal sobre o qual cada técnica atua na arquitetura proposta.

A Tabela 2 revela três achados de honestidade científica, princípio operacionalizado por Wilkinson et al. (2016) sob o atributo *Reusable* dos princípios FAIR. Em primeiro lugar, a redução do custo por comando, em fator dezenove vírgula sete, supera a projeção analítica original de uma ordem de grandeza, indicando que a composição multi-LoRA somada à decodificação especulativa com chaveamento por entropia é multiplicativamente mais eficiente do que a soma de seus componentes individuais. Em segundo lugar, a redução de contingência à nuvem, em fator sete vírgula três, confirma parcialmente a projeção original e mantém o ganho na faixa de uma ordem de grandeza. Em terceiro lugar — e este é o achado mais revelador —, a redução do percentil noventa e nove de latência foi de apenas um vírgula um, significativamente abaixo da projeção. Este resultado motiva a articulação formal apresentada na sub-seção seguinte.

A Figura 4 apresenta a função de distribuição empírica acumulada do percentil 99 sobre as 300 réplicas Monte-Carlo, com o painel esquerdo cobrindo os cenários nominal e de partição (escala linear 1.500–1.850 ms) e o painel direito isolando o cenário de surto (escala linear 100k–400k ms) — opção de visualização adotada porque uma escala logarítmica única colapsaria a região nominal/partição em uma linha vertical, ocultando a separação consistente entre linha de base e proposta (técnica clássica em Glasserman, 2003, Seção 1.5 para visualização de variância empírica em Monte-Carlo).

![](figures/figura-04-ecdf-p99.png)

*Figura 4 — Função de distribuição empírica acumulada do p99 de latência sobre 300 réplicas Monte-Carlo (painéis nominal+partição e surto em escalas separadas).*

A Figura 5 apresenta o diagrama de caixa de validação PACELC (latência sob partição *versus* nominal × linha de base *versus* proposta) com painel adicional para o cenário de surto, confirmando que o chaveamento diferenciado por carga útil da arquitetura proposta mantém latência operacional comparável ao nominal mesmo sob partição injetada no canal de subida (Markov bi-estado com taxa de injeção amostrada, conforme `simulation.py:336-376`).

![](figures/figura-05-pacelc-boxplot.png)

*Figura 5 — Diagrama de caixa de validação PACELC com mediana, intervalo interquartil e bigodes a 1,5× para nominal, partição e surto.*

#### 2.3.3. Conjectura do Pipeline Saturado

A redução modesta do percentil noventa e nove (fator um vírgula um) decorre da saturação empírica observada do encadeamento de borda — condição em que o tempo médio de permanência observado, $W_{\text{obs}} \approx 1{,}29$ s, supera a estimativa inicial $W_{\text{est}} = 250$ ms por fator de aproximadamente cinco vezes. Sob essa saturação, a soma serial de Whisper, preenchimento do LLM e geração de cinquenta *tokens* domina a latência fim-a-fim, independentemente da estratégia de *cache* ou de decodificação especulativa adotada.

A Conjectura do Pipeline Saturado, articulada formalmente no Apêndice B, fundamenta este achado: em encadeamentos borda-nuvem com $L_{\text{edge}} \approx L_{\text{cloud}}$, o percentil 99 da latência total é estruturalmente insensível a reduções da taxa de contingência, decorrente da decomposição de mistura apresentada na Equação (5):

$$
\mathrm{p99}(L_{\text{total}}) \approx p_{fb} \cdot \mathrm{p99}(L_{\text{cloud}}) + (1 - p_{fb}) \cdot \mathrm{p99}(L_{\text{edge}}) \quad (5)
$$

Nesta relação, $p_{fb}$ representa a probabilidade de invocação da contingência de nuvem e os demais termos representam os percentis 99 dos componentes de borda e nuvem isoladamente.

A consequência prescritiva é direta: a alavanca real para reduzir o percentil 99 sob saturação de borda deixa de ser a eliminação da contingência — já reduzida em sete vírgula três vezes — e passa a ser a aceleração do caminho serial $L_{\text{edge}}$. Isso corresponde precisamente aos três habilitadores de plataforma da arquitetura proposta: entendimento de linguagem natural dentro da rede sobre P4, agrupamento compartilhado de *cache* sobre Compute Express Link e roteamento sensível a energia.

#### 2.3.4. Verificação computacional da Pareto-eficiência

A composição completa é formalizada como o **Theorem (Pareto-eficiência da Malha Celular no espaço de design ampliado)**, cujo enunciado decorre da definição do espaço ampliado de arquiteturas dada na Equação (6):

$$
\mathcal{A} = \mathcal{P}(T) \cup \mathcal{A}_{\text{ext}} \quad (6)
$$

Nesta relação, $T$ representa o conjunto das nove técnicas integradas, $\mathcal{P}(T)$ representa o conjunto das partes de $T$ (256 sub-composições válidas após aplicação da restrição rígida de comandos verificáveis $t_6$) e $\mathcal{A}_{\text{ext}}$ representa o subconjunto de sete arquiteturas externas concretas modeladas a partir dos números primários reportados em Splitwise (Patel et al., 2024), DistServe (Zhong et al., 2024), Mooncake (Qin et al., 2025), Sarathi-Serve (Agrawal et al., 2024), vLLM (Kwon et al., 2023), EAGLE-3 (Li et al., 2025) e na composição do núcleo sem habilitadores. O Theorem estabelece que o espaço estendido $\mathcal{A}$ não admite nenhum elemento que Pareto-domine $T$ sob a métrica $S$ aplicada aos cinco eixos $\mathbf{e} = (\text{p99}, p_{fb}, \text{custo}, \text{raio de impacto}, \text{energia})$. O esboço da prova (Lemmas 1–3) e a verificação computacional completa estão apresentados no Apêndice A.

A verificação computacional reproduzível enumera todas as $2^9 = 512$ sub-composições do espaço de design, identifica as 256 válidas que satisfazem o requisito obrigatório de comandos verificáveis sob chaveamento por carga útil e confirma que zero sub-composições Pareto-dominam a composição completa. A composição completa Pareto-domina seis das sete arquiteturas externas testadas e permanece Pareto-incomparável apenas com EAGLE-3, cuja vantagem é restrita à latência analítica de requisição única — resultado científico genuíno alinhado à moldura Pareto-óptima de Recasens et al. (2024) para inferência de Modelos de Linguagem Pequenos, estendido aqui ao domínio borda-nuvem industrial. A análise de sensibilidade Monte-Carlo, com mil realizações e perturbação de mais ou menos vinte por cento nos fatores, confirma que a composição permanece Pareto-óptima em 100% das realizações.

#### 2.3.5. Limitações

Três limitações merecem registro explícito antes da síntese final. A primeira é que a documentação oficial ZenML (2025) reconhece textualmente que o material original Addverb possui caráter estritamente mercadológico, sem métricas auditáveis publicadas — fato que impõe à linha de base o status de modelo plausível calibrado por aproximações de fronteira, não de medição direta. A segunda é a ambiguidade documental entre Convirza Llama 3B e Llama 3.1 8B, que persiste como inconsistência da fonte primária; relatam-se ambas as versões para preservar fidelidade ao registro, sem correção por adivinhação. A terceira é que a ficha de soluções Intel de número 363090-001US encontra-se em triangulação parcial; verificação adicional via canais oficiais Intel e auditoria das páginas de produtos Supermicro estão agendadas para a fase de validação empírica ampliada, e qualquer divergência substantiva deflagrará revisão da Seção 2.2.4. *Ceteris paribus*, a robustez quantitativa da proposta depende criticamente da execução do plano de simulação descrito no repositório público do autor (Flores, 2026), cujas extensões específicas constituem o conteúdo da Seção 3.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
## 3. Considerações Finais

### 3.1. Síntese da contribuição

A análise conduzida ao longo das Seções 2.1, 2.2 e 2.3 sustenta uma proposição central: sob saturação do encadeamento de borda — condição empiricamente observada no caso Addverb com $\rho_{\text{edge}} \to 1$ e $L_{\text{edge}} \approx L_{\text{cloud}}$ —, a alavanca operacional para reduzir o percentil 99 da latência deixa de ser o roteamento à contingência ($p_{fb}$) e passa a ser a aceleração do caminho serial $L_{\text{edge}}$. Esta proposição condicional, articulada como Conjectura do Pipeline Saturado e detalhada no Apêndice B, é fundamentada em decomposição de mistura sobre o modelo Pollaczek-Khinchine para fila M/G/1 e dialoga com a discussão de problemas abertos da intersecção entre teoria de filas e LLMs em Mitzenmacher e Shahout (2025). A validação preditiva da conjectura em sistemas com razão entre as latências de borda e de nuvem distinta de 0,91 — valor empírico observado no Addverb — constitui requisito metodológico para sua promoção a teorema amplo.

A arquitetura Malha Celular de Inferência oferece os mecanismos operacionais que a conjectura prescreve. A camada P4 dentro da rede (Gao et al., 2024) acelera o estágio inicial de detecção de palavra-de-ativação e identificação de idioma descarregando-os para comutadores em *line rate*; a camada CXL 3.0 (Tang et al., 2024; Yang et al., 2026) acelera o estágio de preenchimento via memória partilhada entre AGVs cooperativos da mesma célula; e o roteamento sensível a energia (Niu et al., 2025; Wilhelm et al., 2025) reduz a utilização $\rho_{\text{edge}}$ por instância via redistribuição inteligente de carga. A Pareto-eficiência da composição completa em cinco eixos — latência p99, taxa de contingência, custo por comando, raio de impacto e energia — é estabelecida no Apêndice A por enumeração computacional sobre 256 sub-composições próprias válidas e sete arquiteturas externas modeladas a partir dos números primários reportados em Splitwise (Patel et al., 2024), DistServe (Zhong et al., 2024), Mooncake (Qin et al., 2025), Sarathi-Serve (Agrawal et al., 2024), vLLM (Kwon et al., 2023), EAGLE-3 (Li et al., 2025) e na composição do núcleo sem habilitadores. A composição completa domina seis das sete arquiteturas externas testadas e permanece Pareto-incomparável apenas com EAGLE-3, cuja vantagem é restrita à latência de requisição única.

A validação empírica das seis técnicas do núcleo, conduzida via simulação Salabim de eventos discretos com semente determinística sob três cenários e trezentas réplicas Monte-Carlo de meia hora simulada cada, confirma a redução de contingência à nuvem em fator 7,3 (de 30,02% para 4,10%, com intervalo de confiança de 95%) e a redução de custo por comando em fator 19,7 (de US\$~0,0809 para US\$~0,00410), superando a projeção analítica original de uma ordem de grandeza no eixo custo. A redução do percentil 99 da latência, contudo, alcançou apenas 1,1 vezes — fato que constitui evidência empírica local da Conjectura do Pipeline Saturado, dado que a saturação de borda cola $L_{\text{edge}} \approx L_{\text{cloud}}$ e remove a alavanca de roteamento como preditor do percentil 99. A Lei de Little é validada empiricamente com erro inferior a 1% em todas as réplicas dos cenários nominais, confirmando a consistência matemática do modelo.

### 3.2. Posicionamento no acervo da disciplina

O caso Addverb representa a ponta industrial da convergência entre LLMOps de produção e Internet Industrial das Coisas (IIoT), segmento sistematizado por Qu et al. (2024) em IEEE Communications Surveys & Tutorials sob a taxonomia *Mobile Edge Intelligence* para LLMs. Os desafios mapeados — barreira linguística de noventa e oito idiomas, tempo de manutenção em frotas globais e chaveamento de segurança operacional sob carga útil de duas toneladas — extrapolam o domínio puramente textual de assistentes conversacionais empresariais e situam o trabalho na vanguarda da Indústria 4.0 com sistemas ciberfísicos comandados por inferência de LLM. A aderência à evolução do banco ZenML — de 457 casos documentados em 2024 para mais de 1.200 implantações em 2025 — confirma que o tema é central, não periférico, na maturidade da disciplina.

O trabalho situa-se acima de descrições puramente narrativas dos casos do banco ZenML (ZenML, 2025) — que dominam aproximadamente trinta e oito por cento do acervo em paradigma de geração aumentada por recuperação simples —, contribuindo ao estado da arte em LLMOps de produção e *Mobile Edge Intelligence* aplicado a IIoT por meio de quatro contribuições coordenadas: (i) a verificação computacional reproduzível, por enumeração combinatória sobre o espaço de design ampliado, de que a composição da Malha Celular é Pareto-eficiente em cinco eixos contra 256 sub-composições próprias e sete arquiteturas externas concretas; (ii) a articulação formal da Conjectura do Pipeline Saturado, suportada por modelagem M/G/1 com Pollaczek-Khinchine e decomposição de mistura, que reinterpreta a redução modesta do percentil 99 observada como evidência estrutural local de insensibilidade sob saturação de borda; (iii) a validação empírica via simulação Salabim de eventos discretos das seis técnicas do núcleo sob três cenários e trezentas réplicas Monte-Carlo, com cadeia de *hashes* rastreável documentada em `experiment_provenance.json`; e (iv) a formalização da decisão de chaveamento por carga útil sob *Zero Trust* e dos limites analíticos das nove técnicas integradas. As nove técnicas individuais já existem na literatura de mais alto impacto, com fontes específicas catalogadas na Seção 2.1; a contribuição autoral reside na composição multiplicativa Pareto-eficiente formalmente verificada, na conjectura estrutural que reinterpreta a redução modesta do percentil 99 como evidência empírica de saturação e na arquitetura como plataforma habilitadora nomeada que sintetiza essa composição.

### 3.3. Direções de pesquisa

Seis direções de pesquisa estendem naturalmente o trabalho:

(i) **Validação empírica ampliada.** Expandir a simulação de trezentas para mil réplicas Monte-Carlo e de meia hora para uma hora simulada por réplica, estreitando os intervalos de confiança e aumentando a robustez estatística (metodologia padrão em Glasserman, 2003 e Asmussen & Glynn, 2007).

(ii) **Instrumentação P4.** Implementar o entendimento de linguagem natural dentro da rede via comutadores programáveis P4 (Tofino e Tofino-2) para descarregar estágios triviais de detecção de palavra-de-ativação e identificação de idioma, com redução estimada de cinco a dez milissegundos em latência.

(iii) **Escalonamento CXL 3.0.** Expandir os agrupamentos compartilhados de *cache* entre múltiplos servidores de borda, ampliando a capacidade local de dois para até dezesseis terabytes de agrupamento unificado.

(iv) **Decomposição energética.** Refinar o roteamento sensível a energia com decomposição de *joules* por comando em reconhecimento de fala, LLM de borda, canal de subida, LLM de nuvem e síntese de fala, identificando pontos de otimização energética não óbvios.

(v) **Ablação empírica completa.** Substituir a ablação analítica da Tabela 3 — derivada das fórmulas canônicas dos artigos-âncora — por uma ablação empírica das seis técnicas do núcleo (seis componentes × trezentas réplicas × 1.800 segundos simulados).

(vi) **Calibração contra traços de produção.** Substituir as aproximações de fronteira de ensaios Intel atualmente empregadas em `ExperimentConfig` por distribuições empíricas oriundas de Mooncake-trace (Qin et al., 2025) ou BurstGPT, abrangendo intervalo entre chegadas, tamanho de *prompt* e tempo entre *tokens*.

A validação empírica conjunta dos três habilitadores — P4, CXL e energia — no caso Addverb e a generalização da Conjectura do Pipeline Saturado a outros domínios borda-nuvem LLM industriais constituem as direções de pesquisa naturalmente derivadas, alinhadas aos princípios FAIR de reusabilidade científica formulados por Wilkinson et al. (2016).

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
**Referências**

Abadi, D. J. (2012). 'Consistency tradeoffs in modern distributed database system design: CAP is only part of the story', *IEEE Computer*, vol. 45, no. 2, pp. 37-42. https://doi.org/10.1109/MC.2012.33

Addverb. (2024). *AGV maintenance with generative AI*. Disponível em: https://addverb.com/agv-maintenance-with-generative-ai/ (Acesso em: 06 de maio de 2026).

Agrawal, A., Kedia, N., Panwar, A., Mohan, J., Kwatra, N., Gulavani, B., Tumanov, A., & Ramjee, R. (2024). 'Taming throughput-latency tradeoff in LLM inference with Sarathi-Serve', *Proceedings of the 18th USENIX Symposium on Operating Systems Design and Implementation*. https://arxiv.org/abs/2403.02310

Ainslie, J., Lee-Thorp, J., de Jong, M., Zemlyanskiy, Y., Lebrón, F., & Sanghai, S. (2023). 'GQA: Training generalized multi-query transformer models from multi-head checkpoints', *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pp. 4895-4901. https://doi.org/10.18653/v1/2023.emnlp-main.298

Asmussen, S. & Glynn, P. W. (2007). *Stochastic Simulation: Algorithms and Analysis*. Springer (Stochastic Modelling and Applied Probability, vol. 57). https://doi.org/10.1007/978-0-387-69033-9

Beltagy, I., Peters, M. E., & Cohan, A. (2020). 'Longformer: The long-document transformer'. arXiv preprint arXiv:2004.05150. https://arxiv.org/abs/2004.05150

Brandon, W., Mishra, M., Nrusimha, A., Panda, R., & Kelly, J. R. (2024). 'Reducing transformer key-value cache size with cross-layer attention'. arXiv preprint arXiv:2405.12981. https://arxiv.org/abs/2405.12981

Cai, T., Li, Y., Geng, Z., Peng, H., Lee, J. D., Chen, D., & Dao, T. (2024). 'Medusa: Simple LLM inference acceleration framework with multiple decoding heads'. arXiv preprint arXiv:2401.10774. https://arxiv.org/abs/2401.10774

Chen, C., Borgeaud, S., Irving, G., Lespiau, J.-B., Sifre, L., & Jumper, J. (2023). 'Accelerating large language model decoding with speculative sampling'. arXiv preprint arXiv:2302.01318. https://arxiv.org/abs/2302.01318

Dean, J., & Barroso, L. A. (2013). 'The tail at scale', *Communications of the ACM*, vol. 56, no. 2, pp. 74-80. https://doi.org/10.1145/2408776.2408794

DeepSeek-AI. (2024). 'DeepSeek-V3 Technical Report'. arXiv preprint arXiv:2412.19437. https://arxiv.org/abs/2412.19437

Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). 'QLoRA: Efficient finetuning of quantized LLMs', *Advances in Neural Information Processing Systems 36*. https://arxiv.org/abs/2305.14314

Flores, C. U. (2026). *Cellular Inference Mesh: Salabim DES of edge-cloud LLM inference under PACELC saturation* [Software]. Zenodo. https://doi.org/10.5281/zenodo.20108648 (repositório de código: https://github.com/ulissesflores/cellular-inference-mesh).

Gao, J., Cao, J., Li, Y., Liu, M., Tang, M., Cai, D., & Zhai, E. (2024). 'Sirius: Composing network function chains into P4-capable edge gateways', *Proceedings of the 21st USENIX Symposium on Networked Systems Design and Implementation (NSDI 2024)*, pp. 477-490. https://www.usenix.org/system/files/nsdi24-gao-jiaqi.pdf

Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering*. Springer (Stochastic Modelling and Applied Probability, vol. 53). https://doi.org/10.1007/978-0-387-21617-1

Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., & Chen, W. (2022). 'LoRA: Low-rank adaptation of large language models', *Proceedings of the Tenth International Conference on Learning Representations*. https://openreview.net/forum?id=nZeVKeeFYf9

IEC. (2010). *IEC 61508-1:2010 — Functional safety of electrical/electronic/programmable electronic safety-related systems — Part 1: General requirements*. International Electrotechnical Commission. https://webstore.iec.ch/publication/5515

Intel Corporation. (2024). *Addverb simplifies AGV maintenance with speech-to-text, generative AI* (Solution Brief 363090-001US). Disponível em: https://www.intel.com/content/www/us/en/products/docs/processors/embedded/addverb-llm-edge-solution-brief.html (Acesso em: 06 de maio de 2026).

Kleppmann, M. (2017). *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media. https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/

Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H., Gonzalez, J. E., Zhang, H., & Stoica, I. (2023). 'Efficient memory management for large language model serving with PagedAttention', *Proceedings of the 29th Symposium on Operating Systems Principles*. https://doi.org/10.1145/3600006.3613165

Leviathan, Y., Kalman, M., & Matias, Y. (2023). 'Fast inference from transformers via speculative decoding', *Proceedings of the 40th International Conference on Machine Learning*, *Proceedings of Machine Learning Research* 202, pp. 19274-19286. https://arxiv.org/abs/2211.17192

Li, H., Berger, D. S., Hsu, L., Ernst, D., Zardoshti, P., Novakovic, S., Shah, M., Rajadnya, S., Lee, S., Agarwal, I., Hill, M. D., Fontoura, M., & Bianchini, R. (2023). 'Pond: CXL-based memory pooling systems for cloud platforms', *Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS 2023)*. https://doi.org/10.1145/3575693.3578835

Li, Y., Wei, F., Zhang, C., & Zhang, H. (2025). 'EAGLE-3: Scaling up inference acceleration of large language models via training-time test'. arXiv preprint arXiv:2503.01840. https://arxiv.org/abs/2503.01840

MacCárthaigh, C. (2019). *Shuffle sharding: massive and magical fault isolation*. AWS Builders' Library. Disponível em: https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/ (Acesso em: 06 de maio de 2026).

Mitzenmacher, M. & Shahout, R. (2025). 'Queueing, predictions, and large language models: Challenges and open problems', *Stochastic Systems*. https://doi.org/10.1287/stsy.2025.0106

Niu, C., Zhang, W., Li, J., Zhao, Y., Wang, T., Wang, X., & Chen, Y. (2025). 'TokenPowerBench: Benchmarking the power consumption of LLM inference'. arXiv preprint arXiv:2512.03024. https://arxiv.org/abs/2512.03024

Patel, P., Choukse, E., Zhang, C., Goiri, Í., Shah, A., Maleki, S., & Bianchini, R. (2024). 'Splitwise: Efficient generative LLM inference using phase splitting', *Proceedings of the 51st Annual International Symposium on Computer Architecture*, pp. 118-132. https://doi.org/10.1109/ISCA59077.2024.00019

Qin, R., Li, Z., He, W., Cui, J., Ren, F., Zhang, M., Wu, Y., Zheng, W., & Xu, X. (2025). 'Mooncake: Trading more storage for less computation — A KVCache-centric architecture for serving LLM chatbot', *Proceedings of the 23rd USENIX Conference on File and Storage Technologies (FAST 2025)*. Best Paper Award. https://www.usenix.org/conference/fast25/presentation/qin

Qu, G., Chen, Q., Wei, W., Lin, Z., Chen, X., & Huang, K. (2024). 'Mobile edge intelligence for large language models: A contemporary survey', *IEEE Communications Surveys & Tutorials*. https://arxiv.org/abs/2407.18921

Recasens, P. G., Zhu, Y., Wang, C., Lee, E. K., Tardieu, O., Youssef, A., Torres, J., & Berral, J. L. (2024). 'Towards Pareto optimal throughput in small language model serving', *Proceedings of the 4th Workshop on Machine Learning and Systems (EuroSys 2024 ML4Sys Workshop)*. https://doi.org/10.1145/3642970.3655832

Rescorla, E. (2018). *The Transport Layer Security (TLS) Protocol Version 1.3* (IETF RFC 8446). https://www.rfc-editor.org/rfc/rfc8446

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero trust architecture* (NIST Special Publication 800-207). https://csrc.nist.gov/publications/detail/sp/800-207/final

Shazeer, N. (2019). 'Fast transformer decoding: One write-head is all you need'. arXiv preprint arXiv:1911.02150. https://arxiv.org/abs/1911.02150

Sheng, Y., Cao, S., Li, D., Hooper, C., Lee, N., Yang, S., Chou, C., Zhu, B., Zheng, L., Keutzer, K., Gonzalez, J. E., & Stoica, I. (2024). 'S-LoRA: Serving thousands of concurrent LoRA adapters', *Proceedings of Machine Learning and Systems 6*. https://arxiv.org/abs/2311.03285

Tang, Y., Cheng, R., Zhou, P., Liu, T., Liu, F., Tang, W., Bae, K., Chen, J., Xiang, W., & Shi, R. (2024). 'Exploring CXL-based KV cache storage for LLM serving', *NeurIPS 2024 Workshop on Machine Learning for Systems*. https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). 'Attention is all you need', *Advances in Neural Information Processing Systems 30*, pp. 5998-6008. https://arxiv.org/abs/1706.03762

Wilhelm, P., Wittkopp, T., & Kao, O. (2025). 'Beyond test-time compute strategies: Advocating energy-per-token in LLM inference', *Proceedings of the 5th Workshop on Machine Learning and Systems (EuroMLSys 2025)*. https://doi.org/10.1145/3721146.3721953

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., Blomberg, N., Boiten, J.-W., da Silva Santos, L. B., Bourne, P. E., Bouwman, J., Brookes, A. J., Clark, T., Crosas, M., Dillo, I., Dumon, O., Edmunds, S., Evelo, C. T., Finkers, R., Gonzalez-Beltran, A., Gray, A. J. G., Groth, P., Goble, C., Grethe, J. S., Heringa, J., 't Hoen, P. A. C., Hooft, R., Kuhn, T., Kok, R., Kok, J., Lusher, S. J., Martone, M. E., Mons, A., Packer, A. L., Persson, B., Rocca-Serra, P., Roos, M., van Schaik, R., Sansone, S.-A., Schultes, E., Sengstag, T., Slater, T., Strawn, G., Swertz, M. A., Thompson, M., van der Lei, J., van Mulligen, E., Velterop, J., Waagmeester, A., Wittenburg, P., Wolstencroft, K., Zhao, J., & Mons, B. (2016). 'The FAIR Guiding Principles for scientific data management and stewardship', *Scientific Data*, vol. 3, no. 1, p. 160018. https://doi.org/10.1038/sdata.2016.18

Yang, X., Hu, Q., Li, J., Li, F., Zhu, Y., Zhou, Y., Lin, Q., Dai, J., Kong, Y., Zhang, J., Xu, G., & Liu, Q. (2026). 'Beluga: A CXL-based memory architecture for scalable and efficient LLM KVCache management', *Proceedings of the ACM on Management of Data (SIGMOD/PODS)*. https://doi.org/10.1145/3786627

Yang, Y., Xu, Y., & Jiao, L. (2024). 'A queueing theoretic perspective on low-latency LLM inference with variable token length'. arXiv preprint arXiv:2407.05347. https://arxiv.org/abs/2407.05347

Ye, R., Wang, W., Chai, J., Li, D., Li, Z., Xu, Y., Du, Y., Wang, Y., & Chen, S. (2024). 'OpenFedLLM: Training large language models on decentralized private data via federated learning', *Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining*. https://doi.org/10.1145/3637528.3671582

Yu, G.-I., Jeong, J. S., Kim, G.-W., Kim, S., & Chun, B.-G. (2022). 'Orca: A distributed serving system for transformer-based generative models', *Proceedings of the 16th USENIX Symposium on Operating Systems Design and Implementation*, pp. 521-538. https://www.usenix.org/conference/osdi22/presentation/yu

ZenML. (2025). *LLMOps in production: 457 case studies of what actually works*. Disponível em: https://www.zenml.io/blog/llmops-in-production-457-case-studies-of-what-actually-works (Acesso em: 06 de maio de 2026).

Zhong, Y., Liu, S., Chen, J., Hu, J., Zhu, Y., Liu, X., Jin, X., & Zhang, H. (2024). 'DistServe: Disaggregating prefill and decoding for goodput-optimized large language model serving', *Proceedings of the 18th USENIX Symposium on Operating Systems Design and Implementation*. https://arxiv.org/abs/2401.09670

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
## Apêndice A — Esboço da prova do Theorem (Pareto-eficiência)

A demonstração da Pareto-eficiência da Malha Celular percorre, em três lemas convergentes, dois movimentos analíticos distintos: o primeiro caracteriza o comportamento interno do espaço de sub-composições próprias da arquitetura, e o segundo confronta a composição completa com arquiteturas externas concretas extraídas da literatura de mais alto impacto. A separação responde a uma exigência metodológica — Pareto-eficiência interna por monotonicidade multiplicativa não basta para sustentar a afirmação geral, pois o objeto de comparação relevante para a banca acadêmica é o estado da arte público, não apenas o espaço próprio.

O Theorem enunciado na Seção 2.3.4 estabelece, formalmente, que o espaço de design ampliado $\mathcal{A} = \mathcal{P}(T) \cup \mathcal{A}_{\text{ext}}$ não admite nenhum elemento que Pareto-domine a composição completa $T$ sob a métrica $S$ aplicada aos cinco eixos $\mathbf{e} = (\mathrm{p99}, p_{fb}, \text{custo}, \text{raio de impacto}, \text{energia})$. A prova decompõe-se na seguinte estratégia tripartite: o Lemma 1 estabelece que adicionar técnicas a uma sub-composição apenas reduz ou mantém o escore (monotonicidade), o Lemma 2 reduz o espaço de busca à metade pela exigência operacional rígida da técnica $t_6$ (segurança funcional sob carga útil de duas toneladas), e o Lemma 3 verifica computacionalmente a comparação contra sete arquiteturas externas modeladas por fatores independentes. A conclusão, articulada na Seção A.4, amarra os três lemas e resgata a Pareto-eficiência no espaço ampliado.

### A.1. Lemma 1 — Monotenicidade multiplicativa dos fatores $f_{ij}$

A monotenicidade multiplicativa formaliza, em linguagem técnica, uma intuição operacional simples: se cada técnica integrada à composição contribui com um fator de redução não-positivo em pelo menos um eixo de avaliação, então acrescentar técnicas ao núcleo nunca degrada a posição da arquitetura. O Lemma 1 transforma essa intuição em condição suficiente para Pareto-eficiência interna, sob a hipótese de que as técnicas atuam sobre dimensões ortogonais do estado computacional — hipótese justificada na decomposição apresentada na sequência.

**Enunciado.** Sejam os fatores $f_{ij} \in (0, 1]$ associados a cada técnica $t_i \in T$ e cada eixo $e_j \in \mathbf{e}$, calibrados a partir das fórmulas canônicas dos artigos-âncora (Sheng et al., 2024; DeepSeek-AI, 2024; Brandon et al., 2024; Leviathan, Kalman & Matias, 2023; MacCárthaigh, 2019; Patel et al., 2024; Yang, Hu, Li et al., 2026; Niu et al., 2025). Sob a hipótese de aplicação composicionalmente independente das técnicas, o escore composto para uma sub-composição $T' \subseteq T$ obedece à Equação (A.1):

$$
S(T')_j = S_0(\mathbf{e})_j \cdot \prod_{i \in T'} f_{ij} \quad \text{(A.1)}
$$

Nesta relação, $S_0(\mathbf{e})_j$ representa o escore da linha de base Addverb pública sem nenhuma técnica aplicada no eixo $e_j$. A inclusão de qualquer técnica adicional a uma sub-composição apenas reduz ou mantém o escore (nunca aumenta), pois $f_{ij} \in (0, 1]$.

**Justificação da hipótese de independência composicional.** A independência multiplicativa entre as técnicas do núcleo decorre de sua atuação em dimensões ortogonais do estado computacional, conforme a decomposição abaixo:

- $t_1$ (multi-LoRA federado) atua na dimensão **paramétrica** dos pesos do modelo de borda, modificando apenas as matrizes de adaptação por idioma sem alterar o tensor de chave-valor;
- $t_2$ (cache MLA + janela deslizante + CLA-2) atua na dimensão **espacial** do tensor de chave-valor, decompondo-se a si mesma em três sub-fatores ortogonais — compressão latente (DeepSeek-AI, 2024), truncamento temporal (Beltagy et al., 2020) e compartilhamento entre camadas (Brandon et al., 2024) — cuja independência é demonstrada nos respectivos artigos-âncora;
- $t_3$ (decodificação especulativa) atua na dimensão **temporal** do laço autorregressivo, alterando o número esperado de chamadas ao modelo verificador sem modificar nem os pesos nem o tensor de chave-valor;
- $t_4$ (disagregação preenchimento-geração) atua na dimensão **topológica** da alocação de recursos, separando agrupamentos heterogêneos sem interferir na composição local;
- $t_5$ (isolamento celular por particionamento aleatório) atua na dimensão **combinatória** do mapeamento AGV-trabalhador, ortogonal a qualquer decisão local de cômputo;
- $t_6$ (chaveamento por carga útil) atua na dimensão **decisória** binária por comando, sem custo computacional adicional sobre o caminho de inferência;
- $t_7, t_8, t_9$ (entendimento dentro da rede, agrupamento CXL e roteamento sensível a energia) atuam, respectivamente, nas dimensões de **rede**, **memória compartilhada** e **distribuição de carga** — cada uma claramente disjunta das demais.

A ortogonalidade dimensional implica que o efeito conjunto sobre cada eixo $e_j$ é a composição multiplicativa dos efeitos individuais, satisfazendo a Equação (A.1). Casos potenciais de não-independência (por exemplo, interação entre $t_2$ e $t_3$ via efeito do cache no rascunhador) seriam capturados como termos de interação em uma calibração empírica refinada via ablação sistemática — direção identificada na Seção 3.3 (item v).

**Consequência.** A composição completa $T$ exibe o menor escore analítico em cada eixo $e_j$ entre todas as sub-composições $T' \in \mathcal{P}(T)$. Em outras palavras, nenhuma sub-composição estritamente própria de $T$ pode dominá-la em qualquer eixo individual, e portanto não pode Pareto-dominá-la coletivamente.

### A.2. Lemma 2 — A restrição rígida $t_6$ reduz $\mathcal{P}(T)$ a 256 sub-composições válidas

O Lemma 2 traduz, para o domínio combinatório do espaço de sub-composições, uma exigência de segurança funcional decorrente da norma IEC 61508. A técnica $t_6$ — comandos verificáveis com chaveamento criptográfico diferenciado por carga útil — não é uma alavanca de desempenho discricionária, mas requisito operacional aplicável sempre que a frota inclui veículos cuja massa de carga útil ultrapassa a fronteira regulatória de criticidade. A consequência é uma poda combinatória do espaço de busca: das $2^9 = 512$ sub-composições teoricamente possíveis sobre o conjunto $T$ de nove técnicas, apenas as 256 que contêm $t_6$ são operacionalmente válidas no domínio AGV industrial. A redução simplifica a verificação computacional sem sacrificar generalidade analítica e fundamenta a enumeração efetivamente conduzida em `pareto_proof.py`.

**Enunciado.** A técnica $t_6$ — comandos verificáveis sob chaveamento criptográfico por carga útil — constitui requisito operacional rígido derivado da norma de Segurança Funcional IEC 61508 (IEC, 2010), aplicável a sistemas eletrônicos críticos como o Zippy Tug, cuja carga útil de duas toneladas implica risco físico mensurável em caso de falha. Sub-composições $T'$ tais que $t_6 \notin T'$ são, portanto, invalidamente operacionalizáveis no domínio AGV industrial.

**Consequência.** Dos $2^9 = 512$ subconjuntos possíveis de $T$, exatamente metade contém $t_6$ por simetria combinatória, conforme a Equação (A.2):

$$
|\{T' \in \mathcal{P}(T) : t_6 \in T'\}| = 2^{|T|-1} = 2^8 = 256 \quad \text{(A.2)}
$$

A enumeração computacional efetiva, portanto, percorre apenas as 256 sub-composições que satisfazem o requisito mandatório, reduzindo o espaço de busca em fator de dois sem sacrificar generalidade.

### A.3. Lemma 3 — Pareto-incomparabilidade contra arquiteturas externas modeladas com fatores independentes

A Pareto-eficiência interna ao espaço de sub-composições próprias, estabelecida pelos Lemas 1 e 2, não esgota a obrigação metodológica da prova: faz-se necessário confrontar a composição completa $T$ contra arquiteturas externas concretas, modeladas por fatores derivados independentemente das publicações primárias e não como subconjuntos da matriz $F_{ij}$. A escolha das sete famílias arquiteturais — Splitwise, DistServe, Mooncake, Sarathi-Serve, vLLM, EAGLE-3 e Cellular-sem-habilitadores — cobre as principais classes de design público em inferência de Grandes Modelos de Linguagem (disagregação preenchimento-geração, multi-LoRA, atenção paginada, preenchimentos fragmentados, decodificação especulativa isolada e composição de núcleo sem habilitadores de plataforma). O resultado antecipado é que a Malha Celular Pareto-domina seis das sete arquiteturas e permanece Pareto-incomparável apenas com EAGLE-3 isolada — propriedade desejada da composição multi-eixo, conforme detalhado na consequência abaixo.

**Enunciado.** Sejam $\mathcal{A}_{\text{ext}} = \{$ Splitwise, DistServe, Mooncake, Sarathi-Serve, vLLM, EAGLE-3, Cellular-sem-habilitadores $\}$ as sete arquiteturas externas concretas extraídas da literatura de mais alto impacto em inferência de Grandes Modelos de Linguagem. Cada arquitetura externa é modelada com vetor de fatores $f^{(\text{ext})}_j$ derivado independentemente dos números primários reportados nos respectivos resumos publicados — não como subconjunto da matriz $F_{ij}$ da composição proposta —, eliminando circularidade na comparação.

**Consequência.** A avaliação computacional reproduzível, conduzida em `pareto_proof.py`, demonstra que seis das sete arquiteturas externas são Pareto-dominadas por $T$ (escore inferior ou igual em todos os cinco eixos, estritamente inferior em pelo menos um). A sétima arquitetura, EAGLE-3 isolada, é Pareto-incomparável com $T$: apresenta percentil 99 analítico inferior ($268$ ms, derivado do fator de aceleração 6,5× reportado em Li et al., 2025) mas excede $T$ em quatro outros eixos — taxa de contingência ($p_{fb} = 0{,}30$ contra $0{,}022$), custo (US\$ 0,0809 contra US\$ 0,00261), raio de impacto ($0{,}250$ contra $0{,}0357$) e energia ($7{,}22$ J contra $2{,}88$ J). Nenhuma arquitetura externa, portanto, Pareto-domina $T$. A presença de uma arquitetura Pareto-incomparável (EAGLE-3) é informativa em sentido distinto: indica que o Theorem captura Pareto-eficiência em sentido multi-eixo composto, não dominância universal em qualquer eixo isolado — propriedade desejada da composição multi-objetivo, mas que deve ser apresentada como caracterização do escopo do resultado, não como argumento adicional em favor da composição.

### A.4. Conclusão (Theorem) e verificação computacional

Pelos Lemas 1, 2 e 3, nenhum elemento de $\mathcal{A} = \mathcal{P}(T) \cup \mathcal{A}_{\text{ext}}$ Pareto-domina $T$. A composição completa $T$ é, portanto, Pareto-eficiente no espaço de design ampliado. $\square$

A verificação computacional reproduzível enumera as 256 sub-composições válidas, aplica a função de escore da Equação (A.1), avalia Pareto-dominância par-a-par e confirma zero dominadores de $T$. A análise de sensibilidade Monte-Carlo, com mil realizações sob perturbação multiplicativa $\xi_{ij} \sim \mathrm{Uniform}(0{,}80;\,1{,}25)$ aplicada a cada $f_{ij} < 1$, confirma que a composição permanece Pareto-óptima em $1000/1000$ realizações ($\equiv 100\%$), consoante o registro em `output/pareto_proof.json` rastreável por SHA-256.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
## Apêndice B — Conjectura do Pipeline Saturado: decomposição de mistura

A Conjectura do Pipeline Saturado, articulada na Seção 2.3.3, estabelece que sob saturação da borda — condição empiricamente caracterizada por $\rho_{\text{edge}} \to 1$ e, em particular, $L_{\text{edge}} \approx L_{\text{cloud}}$ no percentil 99 —, a sensibilidade de $\mathrm{p99}(L_{\text{total}})$ a reduções da taxa de contingência $p_{fb}$ é estruturalmente desprezível. Este apêndice apresenta a fundamentação formal da Conjectura em cinco movimentos analíticos articulados: a Seção B.1 retoma o modelo Pollaczek-Khinchine para fila M/G/1 como ferramenta clássica de teoria de filas que captura o comportamento da cauda sob saturação; a Seção B.2 aplica a decomposição de mistura à latência total observada em sistemas borda-nuvem com chaveamento por taxa de contingência; a Seção B.3 deriva a expressão analítica da sensibilidade desprezível sob saturação; a Seção B.4 reporta a validação numérica reproduzível sobre quatro regimes operacionais distintos; e a Seção B.5 registra honestamente o status epistêmico da Conjectura — articulada *post hoc* em diálogo com a discussão de problemas abertos de teoria de filas em inferência LLM apresentada por Mitzenmacher e Shahout (2025) — e antecipa as direções de validação preditiva necessárias para sua promoção a Teorema amplo.

### B.1. Modelo Pollaczek-Khinchine para fila M/G/1

A fórmula de Pollaczek-Khinchine, originalmente derivada na década de 1930 para filas M/G/1 com chegadas Poisson e tempo de serviço de distribuição genérica, fornece a ferramenta clássica para analisar o comportamento da cauda da latência sob carga próxima da capacidade do servidor. No contexto da inferência industrial, a relevância do modelo decorre de três observações empíricas convergentes no caso Addverb: chegadas de comandos de voz seguem processo aproximadamente Poisson (operadores independentes, frequência baixa por veículo), tempo de serviço apresenta distribuição log-normal de cauda pesada (composição serial de Whisper, preenchimento e geração com tempo por *token* variável) e a utilização do servidor de borda observada empiricamente situa-se em $\rho_{\text{edge}} \approx 0{,}96$ — valor que coloca a operação no regime assintótico de saturação descrito pela fórmula.

A fórmula clássica de Pollaczek-Khinchine para fila M/G/1 com tempo de serviço de média $E[S]$ e coeficiente de variação $C_S$ apresenta o tempo médio de espera na Equação (B.1):

$$
E[W] = \frac{\rho \cdot E[S] \cdot (1 + C_S^2)}{2 \cdot (1 - \rho)} \quad \text{(B.1)}
$$

Nesta relação, $\rho = \lambda \cdot E[S]$ representa a utilização do servidor. Quando $\rho \to 1$, o tempo de espera $E[W] \to \infty$ assintoticamente, e a variabilidade do tempo de serviço — capturada por $C_S^2$ — domina o comportamento dos percentis altos da latência total. No caso Addverb, o tempo de serviço log-normal observado tem $C_S \gtrsim 1$, o que infla diretamente o percentil 99 quando $\rho$ aproxima-se da unidade, conforme análise específica para inferência de LLM com tamanho de *token* variável apresentada por Yang, Xu e Jiao (2024).

### B.2. Decomposição de mistura sob saturação

Em sistemas borda-nuvem com chaveamento por taxa de contingência $p_{fb}$, a latência total $L_{\text{total}}$ observada por um comando individual é uma variável aleatória de mistura: com probabilidade $p_{fb}$, $L_{\text{total}} = L_{\text{cloud}}$ (caminho de contingência); com probabilidade $1 - p_{fb}$, $L_{\text{total}} = L_{\text{edge}}$ (caminho de borda). O percentil 99 de uma mistura de duas variáveis aleatórias com tempos de serviço log-normais admite, sob a hipótese local-linear de Glasserman (2003, Seção 1.5) válida quando $\mathrm{p99}(L_{\text{cloud}})$ e $\mathrm{p99}(L_{\text{edge}})$ encontram-se próximos, a aproximação apresentada na Equação (B.2):

$$
\mathrm{p99}(L_{\text{total}}) \approx p_{fb} \cdot \mathrm{p99}(L_{\text{cloud}}) + (1 - p_{fb}) \cdot \mathrm{p99}(L_{\text{edge}}) \quad \text{(B.2)}
$$

A aproximação é uma combinação convexa dos percentis 99 dos componentes, ponderada pela probabilidade de invocação de cada caminho. Sua validade local é discutida por Asmussen e Glynn (2007) sob heterogeneidade de caudas, com refinamento via expansão de Cornish-Fisher disponível como direção futura de aprofundamento metodológico.

### B.3. Sensibilidade desprezível sob saturação

A derivada parcial do percentil 99 da latência total em relação à taxa de contingência decorre diretamente da Equação (B.2) e é apresentada na Equação (B.3):

$$
\frac{\partial \, \mathrm{p99}(L_{\text{total}})}{\partial \, p_{fb}} = \mathrm{p99}(L_{\text{cloud}}) - \mathrm{p99}(L_{\text{edge}}) \quad \text{(B.3)}
$$

Quando $L_{\text{edge}} \approx L_{\text{cloud}}$ — a condição operacional saturada caracterizada empiricamente —, a diferença na Equação (B.3) tende a zero, e portanto a sensibilidade do percentil 99 a reduções de $p_{fb}$ torna-se desprezível. Esta é a expressão analítica precisa da Conjectura: sob saturação de borda, reduzir a contingência não move significativamente a cauda da latência.

### B.4. Validação numérica sobre quatro regimes operacionais

A validação numérica reproduzível, conduzida em `scripts/saturated_pipeline_plot.py`, computa $\mathrm{p99}(L_{\text{total}})$ para $p_{fb} \in [0, 1]$ sob quatro regimes operacionais distintos da razão entre as latências de borda e de nuvem $\{0{,}1;\,0{,}5;\,0{,}91;\,1{,}0\}$. As curvas resultantes — disponíveis em `output/saturated_pipeline.{png,pdf,svg}` — confirmam que a inclinação de $\mathrm{p99}(p_{fb})$ achata-se progressivamente conforme essa razão aproxima-se da unidade. Os pontos empíricos Addverb caem precisamente sobre a curva correspondente a 0,91, não sobre a curva correspondente a 0,1, que prevaleceria em ausência de saturação.

A predição numérica do modelo é apresentada na Tabela B.1.

*Tabela B.1 — Predição da Conjectura do Pipeline Saturado contra observação empírica Addverb (regime $L_\text{edge}/L_\text{cloud} = 0{,}91$).*

| **Cenário** | **$p_{fb}$** | **Modelo (Eq. B.2), ms** | **Empírico Addverb, ms** | **Erro relativo** |
|---|---:|---:|---:|---:|
| Linha de base | 0,300 | 1.625 | 1.740 | 6,6% |
| Proposta | 0,041 | 1.583 | 1.576 | 0,4% |
| Razão de redução | — | 1,03× | 1,10× | — |

A redução prevista pelo modelo (fator 1,03×) é consistente com a redução empírica observada (fator 1,10×) na ordem de grandeza, e ambas distam abissalmente do fator 7,3× que ingenuamente se esperaria sob a hipótese (falsa em regime saturado) de proporcionalidade direta entre $p_{fb}$ e $\mathrm{p99}$. A divergência residual entre modelo e empírico é atribuível a (i) o fato de PD-disagg (Mooncake) reduzir marginalmente $\mathrm{p99}(L_{\text{cloud}})$ na arquitetura proposta — efeito não modelado na aproximação local-linear — e (ii) a heterogeneidade de caudas log-normais entre os componentes de borda e nuvem.

### B.5. Status epistêmico e direções de validação

A Conjectura é apresentada como tal — e não como Teorema — por refletir suporte local: foi articulada *post hoc* a partir do gap entre a projeção analítica de Theorem (fator 4,77× para $\mathrm{p99}$) e a observação empírica Addverb (fator 1,10×) sob `seed = 42`. A explicação via decomposição de mistura sobre Pollaczek-Khinchine fundamenta o achado em teoria de filas clássica, dialogando com a discussão de problemas abertos na intersecção entre teoria de filas e LLMs em Mitzenmacher e Shahout (2025). A validação preditiva — não meramente explicativa *post hoc* — em sistemas cuja razão entre as latências de borda e de nuvem seja distinta de 0,91 (outros fornecedores de AGV, IoT manufatureiro, inferência LLM em telemedicina) constitui requisito metodológico para a promoção da Conjectura a Teorema amplo.
