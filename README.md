#Dynamic-GS — CitizenTech: Rotas e Lotação de Ônibus#

Integrantes
Lucas Mesquita Massoni — RM561686
Felipe Balbino Murad — RM562347

1. O problema

O projeto parte de uma dor real do transporte público: o passageiro não sabe se, ao chegar no ponto, conseguirá embarcar no próximo ônibus ou se ele já estará cheio. Sem essa informação, a pessoa perde tempo esperando um veículo que não a comporta, ou embarca em condições desconfortáveis.

O Dynamic-GS resolve isso com um simulador que responde a três perguntas: qual é o melhor caminho entre duas paradas, quanto tempo esse trajeto leva e qual é o nível de lotação de cada trecho no horário escolhido.

2. Técnicas de Programação Dinâmica aplicadas

O enunciado pede a aplicação de algumas das técnicas listadas: memoização, tabulação e grafos. O projeto usa as três.

2.1 Grafos

A rede de transporte é modelada como um grafo não direcionado e ponderado.

Cada parada é um nó. Cada trecho entre duas paradas consecutivas de uma linha é uma aresta, cujo peso é o tempo de deslocamento em minutos. Como as linhas se cruzam em paradas compartilhadas, o grafo permite que o algoritmo encontre caminhos que trocam de linha — as baldeações.

A construção está em core/grafo.py e core/rotas.py. O algoritmo de busca é o Dijkstra, que encontra o caminho de menor tempo entre origem e destino.

Complexidade:

O((V+E)logV)O((V+E)logV)

com fila de prioridade, onde

V é o número de paradas e

E o número de trechos.

2.2 Tabulação

A lotação de cada trecho é calculada por tabulação: a tabela é preenchida uma única vez, em ordem, e cada posição depende apenas da anterior.

A regra é simples:

ocupacão[i]= ocupacão[i−1] + embarques[i] − desembarques[i] 

Isso significa que a ocupação de uma parada é a ocupação da parada anterior, mais quem entrou, menos quem saiu. O valor nunca fica negativo, porque não existe passageiro com saldo devedor.

A grande vantagem é a eficiência: preencher a tabela custa

O(n), 

e depois cada consulta custa

O(1).

A alternativa ingênua — recalcular a soma desde o início a cada consulta — custa

O(n)

por consulta, o que vira

O(n^2)

para consultar todas as paradas.
A implementação está em tabular_lotacao, em core/lotacao.py.

2.3 Memoização
O cálculo de rotas é memoizado com cache. A primeira consulta entre duas paradas executa o Dijkstra; as seguintes, com a mesma origem e destino, retornam o resultado guardado sem recalcular.

Isso importa porque o usuário costuma alternar entre as mesmas combinações de origem e destino enquanto muda o horário e o dia. Sem memoização, cada interação reconstruiria o grafo e rodaria o algoritmo de novo.

A comparação entre a versão ingênua e a tabulada está em benchmark.py, que mede o tempo das duas abordagens e evidencia o ganho.

3. Funcionalidades implementadas

3.1 Cálculo de rota entre paradas

O usuário escolhe origem e destino e o sistema retorna o caminho de menor tempo, com a lista de trechos, a linha usada em cada trecho e o tempo de cada deslocamento.

3.2 Mapa interativo com a rota desenhada

O trajeto é desenhado sobre o mapa de São Paulo. Cada trecho aparece com a cor da sua linha, então uma rota com baldeação mostra visualmente onde a troca acontece. As paradas do caminho aparecem destacadas em azul, as demais em cinza.

3.3 Seleção de dia da semana e horário de partida

A barra lateral permite escolher entre dia útil, sábado e domingo, além do horário de partida. A lotação muda conforme essas duas escolhas.

3.4 Interpolação de lotação por horário

O histórico de lotação é registrado em blocos de horário — 06h, 07h, 12h, 18h e 22h nos dias úteis. Para responder a um horário que cai entre dois blocos, o sistema interpola linearmente a ocupação de cada parada entre os blocos vizinhos.

Se o usuário pede 14:45, o cálculo usa a distância proporcional entre o bloco das 12h e o das 18h. O resultado é uma lotação estimada coerente com a curva de demanda, e não um valor fixo.

3.5 Classificação de lotação

Cada trecho recebe um dos três estados, com base no percentual de ocupação de um ônibus de 60 lugares:

Vazio — abaixo de 50%
Parcial — entre 50% e 85%
Cheio — acima de 85%
O app exibe esses estados com cores distintas, o que permite ler a situação de um trajeto inteiro rapidamente.

3.6 Itinerário completo por linha

Clicando em uma linha, o usuário vê todas as paradas na ordem, o horário de cada uma e a lotação estimada naquele ponto. É a visão de ponta a ponta da linha, útil para planejar a viagem inteira.

3.7 Validação de horário de operação

Cada tipo de dia tem uma janela de operação — por exemplo, das 05:30 às 23:30 nos dias úteis. Se o usuário pedir um horário fora dessa janela, o sistema informa que não há ônibus disponível e mostra a primeira e a última partida do dia.

3.8 Veredito sobre o trajeto

Ao final, o sistema resume a situação da rota: se há algum trecho cheio, recomenda esperar o próximo ônibus; se há vários trechos parciais, avisa que a viagem será apertada; se há folga, confirma que é uma boa opção.

3.9 Benchmark de desempenho

O arquivo benchmark.py compara o tempo de execução da abordagem ingênua com a tabulada, demonstrando na prática o ganho de eficiência da Programação Dinâmica.

4. Estrutura do projeto
Dynamic-GS/
├── core/
│   ├── __init__.py
│   ├── grafo.py          # Estrutura do grafo e Dijkstra
│   ├── lotacao.py        # Tabulação e interpolação de lotação
│   ├── operacao.py       # Janela de operação e validação de horário
│   └── rotas.py          # Integração entre grafo e lotação
├── data/
│   ├── paradas.json      # Coordenadas e nomes das paradas
│   ├── linhas.json       # Itinerário e tempo entre paradas
│   └── historico_lotacao.csv  # Histórico de embarques e desembarques
├── app_streamlit.py      # Interface visual
├── app.py                # Versão em linha de comando
├── benchmark.py          # Comparação de desempenho
├── gerador_dados.py      # Geração do histórico sintético
├── requirements.txt
└── README.md

5. Como executar

Instale as dependências:

pip install -r requirements.txt

Gere o histórico de lotação:

python gerador_dados.py

Suba a interface:

streamlit run app_streamlit.py

Para rodar a versão em linha de comando:

python app.py

Para ver a comparação de desempenho:

python benchmark.py

6. Escolha das técnicas e justificativa

A combinação das três técnicas não é acidental — cada uma resolve uma parte distinta do problema.

O grafo é a estrutura natural para uma rede de transporte, porque o problema é essencialmente encontrar o melhor caminho em uma malha com conexões. Nenhuma estrutura linear representaria as baldeações corretamente.

A tabulação é a escolha certa para a lotação porque o cálculo é sequencial por natureza: a ocupação de uma parada depende da anterior. Preencher a tabela uma vez e consultar em tempo constante é a solução mais eficiente possível para esse formato de dado.

A memoização evita trabalho repetido em consultas sucessivas, o que é o padrão real de uso — o usuário testa vários horários para a mesma rota.

Juntas, as três cobrem o ciclo completo: modelar a rede, calcular a lotação e responder rápido.

7. Dados

O histórico de lotação é sintético, gerado por gerador_dados.py com curva de demanda realista. Os picos da manhã (07h) e da tarde (18h) concentram a maior ocupação, chegando à capacidade máxima. O meio-dia e o fim da noite ficam na faixa de vazio. Sábado e domingo têm demanda intermediária.

O modelo de geração usa embarque inicial alto no pico e taxa de renovação nos trechos intermediários, com teto na capacidade do veículo. Isso produz uma curva que se comporta como a de um sistema real, sem números fisicamente impossíveis.