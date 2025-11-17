# 🍕 Pega Aí - Protótipo Funcional

## 📖 Sobre o Projeto

**Pega Aí** é uma plataforma que conecta estabelecimentos comerciais com excedente de produção diária a consumidores interessados em adquirir alimentos de qualidade por preços reduzidos, combatendo o desperdício e promovendo consumo consciente.

### Objetivos

- Reduzir desperdício de alimentos
- Gerar receita incremental para estabelecimentos
- Oferecer opções acessíveis para consumidores
- Promover sustentabilidade e consumo consciente

---

## Arquitetura do Protótipo

```
pega-ai-prototipo/
│
├── database.py          # Gerenciamento do banco SQLite
├── popular_dados.py     # Script de população com dados realistas
├── streamlit_app.py     # Interface principal (fluxos de usuário)
├── analytics.py         # Dashboard de análises estatísticas
├── requirements.txt     # Dependências Python
├── README.md           # Esta documentação
└── pega_ai.db          # Banco de dados SQLite (gerado automaticamente)
```

### 🔧 Tecnologias Utilizadas

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Banco de Dados** | SQLite | Zero configuração, portável, ideal para protótipos |
| **Backend** | Python | Linguagem versátil para prototipagem e análises |
| **Interface** | Streamlit | Framework rápido para criar interfaces web |
| **Visualizações** | Plotly | Gráficos interativos de alta qualidade |
| **Análises** | Pandas + SciPy | Estatísticas descritivas e inferenciais |

---

## Como Executar

### **Opção 1: Rodar localmente**

```bash
# 1. Clonar repositório
git clone https://github.com/arthurezende/pega_ai
cd pega_ai

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Popular banco de dados
python popular_dados.py

# 5. Executar aplicação
streamlit run streamlit_app.py
```

### **Opção 2: Streamlit Cloud (Deploy Online)**

1. Suba o código para GitHub
2. Acesse [Streamlit Cloud](https://streamlit.io/cloud)
3. Conecte seu repositório
4. Deploy automático!

---

## Funcionalidades Implementadas

### **Fluxo Consumidor**

- Cadastro e login simplificado
- Visualização de ofertas com filtros (categoria, preço)
- Detalhes da oferta (desconto, horário, estoque)
- Reserva de caixa surpresa
- Geração de código de retirada (simulação de QR Code)
- Histórico de pedidos

### **Fluxo Estabelecimento**

- Cadastro e login
- Criação de ofertas (título, preço, estoque, horário)
- Dashboard com métricas (pedidos, receita)
- Listagem de pedidos recebidos
- Validação de código de retirada

### **Analytics (Dashboard Estatístico)**

- KPIs principais (ofertas, pedidos, receita, economia)
- Análises descritivas:
  - Distribuição de pedidos por status
  - Ofertas por categoria
  - Ticket médio e desvio padrão
  - Análise de descontos
  - Evolução temporal
- Análises inferenciais:
  - Correlação de Pearson (preço vs vendas)
  - Teste ANOVA (categorias vs taxa de venda)
  - Intervalos de confiança

---

## Estrutura do Banco de Dados

### **Entidades Principais**

```sql
usuarios
├── id (PK)
├── nome
├── email (UNIQUE)
├── senha (hash SHA256)
├── tipo (consumidor | estabelecimento)
└── telefone

estabelecimentos
├── id (PK)
├── usuario_id (FK → usuarios)
├── nome_fantasia
├── cnpj
├── endereco
├── latitude
└── longitude

ofertas
├── id (PK)
├── estabelecimento_id (FK → estabelecimentos)
├── titulo
├── categoria
├── preco_original
├── preco_venda
├── estoque_inicial
├── estoque_atual
├── horario_retirada_inicio
└── horario_retirada_fim

pedidos
├── id (PK)
├── consumidor_id (FK → usuarios)
├── oferta_id (FK → ofertas)
├── valor_total
├── codigo_retirada (UNIQUE)
├── status (reservado | pago | retirado | cancelado)
└── criado_em

avaliacoes
├── id (PK)
├── pedido_id (FK → pedidos)
├── nota (1-5)
└── comentario
```

---

## Dados Populados

O script `popular_dados.py` cria:

- **10 estabelecimentos** (diferentes categorias e localizações em SP)
- **50 consumidores** (dados realistas com Faker)
- **30-40 ofertas** (preços, descontos, horários variados)
- **80-100 pedidos** (simulando histórico com diferentes status)
- **20 avaliações** (notas e comentários)

### **Credenciais de Teste**

```
Consumidor:
Email: consumidor1@email.com
Senha: senha123

Estabelecimento:
Email: estabelecimento1@pegaai.com
Senha: senha123
```

---

## Análises Estatísticas Implementadas

### **Análises Descritivas**

1. **Medidas de Tendência Central**: Média, mediana, moda
2. **Medidas de Dispersão**: Desvio padrão, variância, amplitude
3. **Distribuições**: Histogramas, box plots, gráficos de pizza
4. **Séries Temporais**: Evolução de pedidos ao longo do tempo

### **Análises Inferenciais**

1. **Teste de Correlação de Pearson**
   - H₀: Não há correlação entre preço e vendas
   - Nível de significância: α = 0.05

2. **Teste ANOVA (ou t-test)**
   - H₀: Não há diferença entre categorias
   - Interpretação de p-valor e estatística F/t

---

## Entregáveis do Projeto

### **a) Protótipo Funcional**
- Interface Streamlit com fluxos de compra/retirada
- Simulação de QR Code (código alfanumérico)
- CRUD completo de ofertas e pedidos

### **b) Scripts de População**
- `database.py`: Criação do schema
- `popular_dados.py`: Inserção de dados realistas

### **c) Análises Estatísticas**
- Dashboard completo em `analytics.py`
- Descritivas: KPIs, distribuições, tendências
- Inferenciais: correlações, testes de hipótese

### **d) Visualizações**
- Gráficos interativos com Plotly
- Dashboards responsivos
- Filtros dinâmicos

---

## Metodologia de Análise

### **Correlação de Pearson**

Mede a força e direção da relação linear entre duas variáveis:

```python
correlation, p_value = stats.pearsonr(preco, vendas)
```

- **r > 0**: Correlação positiva
- **r < 0**: Correlação negativa
- **|r| → 1**: Correlação forte
- **p-valor < 0.05**: Estatisticamente significativa

### **Teste ANOVA**

Compara médias de 3+ grupos:

```python
f_stat, p_value = stats.f_oneway(grupo1, grupo2, grupo3)
```

- **p-valor < 0.05**: Rejeita H₀ (há diferença entre grupos)

---

## Limitações e Melhorias Futuras

### **Limitações do Protótipo**

-  Sem autenticação real (senhas em hash, mas sem JWT)
-  Sem gateway de pagamento (simulado)
-  Sem geolocalização real (coordenadas fixas)
-  Sem notificações push
-  QR Code simulado (texto), não gráfico

### **Próximos Passos (MVP Real)**

1. **Backend robusto**: FastAPI + PostgreSQL + Redis
2. **Autenticação**: JWT + OAuth2
3. **Pagamentos**: Integração com Pagar.me/Stripe
4. **Geolocalização**: PostGIS + Google Maps API
5. **QR Code real**: Biblioteca qrcode + validação por câmera
6. **Deploy**: AWS/GCP com CI/CD

---

## Equipe

- **Arthur Despíndola Rezende** - RA: 2024022394
- **Marcos Rogério Vieira de Araújo Filho** - RA: 2024022429
- **Tatiana Popp de Souza Lima** - RA: 2024022365
- **Victória Silva de Andrade Munoz** - RA: 2024022347

**Curso**: Ciência de Dados e Inteligência Artificial - 3º Semestre  
**Instituição**: Faculdade Exame

---

## Referências

1. **Fowler, M.** (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.
2. **Kleppmann, M.** (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
3. **Streamlit Documentation**. Disponível em: https://docs.streamlit.io
4. **Plotly Python**. Disponível em: https://plotly.com/python/
5. **Too Good To Go** (Benchmark). Disponível em: https://toogoodtogo.com

---

## Licença

Este é um projeto acadêmico desenvolvido para fins educacionais.

---

## Agradecimentos

Agradecemos à Faculdade Exame pelo suporte e orientação durante o desenvolvimento deste projeto integrado.

---
