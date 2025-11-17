import streamlit as st
from database import Database
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Pega Aí - Protótipo",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .oferta-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #4CAF50;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .status-reservado {
        background-color: #FFF9C4;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-retirado {
        background-color: #C8E6C9;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-cancelado {
        background-color: #FFCDD2;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar banco
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Inicializar session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Função de logout
def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# ============= TELA DE LOGIN =============
def tela_login():
    st.markdown('<div class="main-header">🍕 Pega Aí</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Combata o desperdício, economize e ganhe!</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Cadastro"])
        
        with tab1:
            st.subheader("Entrar no Sistema")
            
            email = st.text_input("E-mail", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🚀 Entrar", use_container_width=True):
                    if email and senha:
                        user = db.autenticar_usuario(email, senha)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.success(f"Bem-vindo(a), {user['nome']}!")
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos")
                    else:
                        st.warning("Preencha todos os campos")
            
            with col_btn2:
                if st.button("🧪 Login Demo", use_container_width=True):
                    # Login rápido para demonstração
                    user = db.autenticar_usuario("consumidor1@email.com", "senha123")
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
            
            st.info("💡 **Demo Rápido**: consumidor1@email.com / senha123")
        
        with tab2:
            st.subheader("Criar Conta")
            
            tipo = st.radio("Tipo de conta", ["Consumidor", "Estabelecimento"], horizontal=True)
            
            nome = st.text_input("Nome completo", key="cadastro_nome")
            email_cadastro = st.text_input("E-mail", key="cadastro_email")
            senha_cadastro = st.text_input("Senha", type="password", key="cadastro_senha")
            telefone = st.text_input("Telefone (opcional)", key="cadastro_telefone")
            
            if st.button("📝 Criar Conta", use_container_width=True):
                if nome and email_cadastro and senha_cadastro:
                    user_id = db.criar_usuario(
                        nome=nome,
                        email=email_cadastro,
                        senha=senha_cadastro,
                        tipo=tipo.lower(),
                        telefone=telefone if telefone else None
                    )
                    
                    if user_id:
                        if tipo == "Estabelecimento":
                            st.success("✅ Conta criada! Complete seu perfil abaixo:")
                            
                            with st.form("completar_estabelecimento"):
                                nome_fantasia = st.text_input("Nome do Estabelecimento")
                                cnpj = st.text_input("CNPJ")
                                endereco = st.text_input("Endereço completo")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    latitude = st.number_input("Latitude", value=-23.550520, format="%.6f")
                                with col2:
                                    longitude = st.number_input("Longitude", value=-46.633308, format="%.6f")
                                
                                if st.form_submit_button("Completar Cadastro"):
                                    est_id = db.criar_estabelecimento(
                                        usuario_id=user_id,
                                        nome_fantasia=nome_fantasia,
                                        cnpj=cnpj,
                                        endereco=endereco,
                                        latitude=latitude,
                                        longitude=longitude
                                    )
                                    if est_id:
                                        st.success("🎉 Estabelecimento cadastrado com sucesso!")
                                        st.info("Faça login para continuar")
                        else:
                            st.success("✅ Conta criada com sucesso! Faça login para continuar.")
                    else:
                        st.error("❌ E-mail já cadastrado")
                else:
                    st.warning("Preencha todos os campos obrigatórios")

# ============= ÁREA DO CONSUMIDOR =============
def area_consumidor():
    st.sidebar.title(f"👤 {st.session_state.user['nome']}")
    st.sidebar.info("**Perfil:** Consumidor")
    
    menu = st.sidebar.radio(
        "Menu",
        ["🏠 Descobrir Ofertas", "🛒 Meus Pedidos", "❓ Como Funciona"],
        key="menu_consumidor"
    )
    
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
    
    if menu == "🏠 Descobrir Ofertas":
        tela_descobrir_ofertas()
    elif menu == "🛒 Meus Pedidos":
        tela_meus_pedidos()
    else:
        tela_como_funciona()

def tela_descobrir_ofertas():
    st.title("🔍 Ofertas Disponíveis")
    st.markdown("**Encontre caixas surpresa perto de você!**")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categorias = ["Todas", "Padaria", "Restaurante", "Hortifrúti", "Confeitaria", "Mercado", "Pizzaria"]
        filtro_categoria = st.selectbox("📂 Categoria", categorias)
    
    with col2:
        preco_max = st.slider("💰 Preço máximo", 5, 50, 50)
    
    with col3:
        ordenacao = st.selectbox("🔄 Ordenar por", ["Mais recentes", "Menor preço", "Maior desconto"])
    
    # Buscar ofertas
    ofertas = db.listar_ofertas_ativas()
    
    # Aplicar filtros
    if filtro_categoria != "Todas":
        ofertas = [o for o in ofertas if o['categoria'] == filtro_categoria]
    
    ofertas = [o for o in ofertas if o['preco_venda'] <= preco_max]
    
    # Ordenação
    if ordenacao == "Menor preço":
        ofertas = sorted(ofertas, key=lambda x: x['preco_venda'])
    elif ordenacao == "Maior desconto":
        ofertas = sorted(ofertas, key=lambda x: (1 - x['preco_venda']/x['preco_original']), reverse=True)
    
    st.markdown(f"**{len(ofertas)} ofertas encontradas**")
    
    # Exibir ofertas
    for oferta in ofertas:
        desconto = int((1 - oferta['preco_venda'] / oferta['preco_original']) * 100)
        
        with st.container():
            st.markdown('<div class="oferta-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🍽️ {oferta['titulo']}")
                st.markdown(f"**📍 {oferta['estabelecimento']}**")
                st.markdown(f"_{oferta['endereco']}_")
                
                if oferta['descricao']:
                    st.markdown(f"💬 {oferta['descricao']}")
                
                st.markdown(f"⏰ **Retirada:** {oferta['horario_inicio']} às {oferta['horario_fim']}")
                st.markdown(f"📦 **Estoque:** {oferta['estoque']} unidades")
            
            with col2:
                st.markdown(f"### ~~R$ {oferta['preco_original']:.2f}~~")
                st.markdown(f"## 💚 R$ {oferta['preco_venda']:.2f}")
                st.success(f"**{desconto}% OFF**")
                
                # Prevenir múltiplas reservas com session_state
                if f"reservando_{oferta['id']}" not in st.session_state:
                    st.session_state[f"reservando_{oferta['id']}"] = False
                
                if st.button("➕ Reservar", key=f"reservar_{oferta['id']}", use_container_width=True, disabled=st.session_state[f"reservando_{oferta['id']}"]):
                    st.session_state[f"reservando_{oferta['id']}"] = True
                    
                    pedido = db.criar_pedido(
                        consumidor_id=st.session_state.user['id'],
                        oferta_id=oferta['id'],
                        quantidade=1
                    )
                    
                    if pedido:
                        st.success(f"✅ Reserva confirmada!")
                        st.info(f"**Código de retirada:** `{pedido['codigo_retirada']}`")
                        st.balloons()
                        st.session_state[f"reservando_{oferta['id']}"] = False
                        st.rerun()
                    else:
                        st.error("❌ Oferta esgotada ou erro na reserva")
                        st.session_state[f"reservando_{oferta['id']}"] = False
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

def tela_meus_pedidos():
    st.title("📦 Meus Pedidos")
    
    pedidos = db.listar_pedidos_consumidor(st.session_state.user['id'])
    
    if not pedidos:
        st.info("Você ainda não fez nenhum pedido. Que tal explorar as ofertas disponíveis?")
        return
    
    # Filtro por status
    status_filtro = st.multiselect(
        "Filtrar por status",
        ["reservado", "pago", "retirado", "cancelado"],
        default=["reservado", "pago", "retirado"]
    )
    
    pedidos_filtrados = [p for p in pedidos if p['status'] in status_filtro]
    
    st.markdown(f"**{len(pedidos_filtrados)} pedidos encontrados**")
    
    for pedido in pedidos_filtrados:
        status_class = f"status-{pedido['status']}"
        
        with st.expander(f"🎫 {pedido['oferta']} - {pedido['estabelecimento']}", expanded=(pedido['status'] == 'reservado')):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Status:** <span class='{status_class}'>{pedido['status'].upper()}</span>", unsafe_allow_html=True)
                st.markdown(f"**Valor:** R$ {pedido['valor']:.2f}")
                st.markdown(f"**Data:** {pedido['data']}")
                st.markdown(f"**Local:** {pedido['endereco']}")
                st.markdown(f"**Horário de retirada:** {pedido['horario_inicio']} às {pedido['horario_fim']}")
            
            with col2:
                if pedido['status'] in ['reservado', 'pago']:
                    st.markdown("### 📱 QR Code")
                    st.code(pedido['codigo'], language=None)
                    st.caption("Apresente este código no estabelecimento")
                    
                    # Botão de cancelamento
                    if st.button("🗑️ Cancelar Pedido", key=f"cancelar_{pedido['id']}", type="secondary"):
                        resultado = db.cancelar_pedido(pedido['id'])
                        if resultado['sucesso']:
                            st.success(resultado['mensagem'])
                            if resultado.get('pagamento_estornado'):
                                st.info("💰 Pagamento estornado com sucesso")
                            st.rerun()
                        else:
                            st.error(resultado['mensagem'])

def tela_como_funciona():
    st.title("❓ Como Funciona o Pega Aí")
    
    st.markdown("""
    ## 🌟 Bem-vindo ao Pega Aí!
    
    Uma plataforma que conecta você a **alimentos de qualidade com preços reduzidos**, 
    ajudando a combater o desperdício e promovendo consumo consciente.
    
    ### 📱 Passo a Passo:
    
    1. **🔍 Descubra** ofertas de estabelecimentos perto de você
    2. **🛒 Reserve** sua caixa surpresa com desconto de até 70%
    3. **📦 Retire** no horário combinado apresentando seu código
    4. **⭐ Avalie** sua experiência e ajude outros usuários
    
    ### 💡 Dicas:
    
    - Fique atento aos horários de retirada
    - Ofertas limitadas: reserve rápido!
    - Caixas surpresa podem variar, mas a qualidade é garantida
    - Apoie estabelecimentos locais e economize
    
    ### 🌱 Impacto:
    
    - Reduz desperdício de alimentos
    - Economia para consumidores
    - Receita extra para estabelecimentos
    - Consumo sustentável
    """)

# ============= ÁREA DO ESTABELECIMENTO =============
def area_estabelecimento():
    st.sidebar.title(f"🏪 {st.session_state.user['nome']}")
    st.sidebar.info("**Perfil:** Estabelecimento")
    
    # Verificar se já tem perfil de estabelecimento
    est_id = db.get_estabelecimento_id(st.session_state.user['id'])
    
    if not est_id:
        st.warning("⚠️ Complete seu cadastro de estabelecimento primeiro")
        completar_cadastro_estabelecimento()
        return
    
    menu = st.sidebar.radio(
        "Menu",
        ["📊 Dashboard", "➕ Nova Oferta", "📦 Pedidos", "✅ Validar Retirada"],
        key="menu_estabelecimento"
    )
    
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
    
    if menu == "📊 Dashboard":
        tela_dashboard(est_id)
    elif menu == "➕ Nova Oferta":
        tela_nova_oferta(est_id)
    elif menu == "📦 Pedidos":
        tela_pedidos_estabelecimento(est_id)
    else:
        tela_validar_retirada()

def completar_cadastro_estabelecimento():
    st.title("🏪 Complete seu Cadastro")
    
    with st.form("completar_estabelecimento"):
        nome_fantasia = st.text_input("Nome do Estabelecimento *")
        cnpj = st.text_input("CNPJ")
        endereco = st.text_area("Endereço completo *")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=-23.550520, format="%.6f")
        with col2:
            longitude = st.number_input("Longitude", value=-46.633308, format="%.6f")
        
        if st.form_submit_button("💾 Salvar", use_container_width=True):
            if nome_fantasia and endereco:
                est_id = db.criar_estabelecimento(
                    usuario_id=st.session_state.user['id'],
                    nome_fantasia=nome_fantasia,
                    cnpj=cnpj,
                    endereco=endereco,
                    latitude=latitude,
                    longitude=longitude
                )
                if est_id:
                    st.success("✅ Estabelecimento cadastrado com sucesso!")
                    st.rerun()
            else:
                st.error("Preencha os campos obrigatórios")

def tela_dashboard(est_id):
    st.title("📊 Dashboard")
    
    # KPIs
    conn = db.get_connection()
    
    # Total de pedidos
    total_pedidos = pd.read_sql(f"""
        SELECT COUNT(*) as total
        FROM pedidos p
        JOIN ofertas o ON p.oferta_id = o.id
        WHERE o.estabelecimento_id = {est_id}
    """, conn)['total'][0]
    
    # Receita total
    receita = pd.read_sql(f"""
        SELECT COALESCE(SUM(p.valor_total), 0) as total
        FROM pedidos p
        JOIN ofertas o ON p.oferta_id = o.id
        WHERE o.estabelecimento_id = {est_id} AND p.status = 'retirado'
    """, conn)['total'][0]
    
    # Ofertas ativas
    ofertas_ativas = pd.read_sql(f"""
        SELECT COUNT(*) as total
        FROM ofertas
        WHERE estabelecimento_id = {est_id} AND status = 'ativa' AND estoque_atual > 0
    """, conn)['total'][0]
    
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Total de Pedidos", total_pedidos)
    
    with col2:
        st.metric("💰 Receita Gerada", f"R$ {receita:.2f}")
    
    with col3:
        st.metric("🎯 Ofertas Ativas", ofertas_ativas)
    
    st.markdown("---")
    st.info("💡 Cadastre ofertas para começar a vender e combater o desperdício!")

def tela_nova_oferta(est_id):
    st.title("➕ Criar Nova Oferta")
    
    with st.form("nova_oferta"):
        col1, col2 = st.columns(2)
        
        with col1:
            titulo = st.text_input("Título da Oferta *")
            categoria = st.selectbox("Categoria *", 
                ["Padaria", "Restaurante", "Hortifrúti", "Confeitaria", "Mercado", "Pizzaria"])
            preco_original = st.number_input("Preço Original (R$) *", min_value=1.0, value=30.0, step=0.5)
            preco_venda = st.number_input("Preço de Venda (R$) *", min_value=1.0, value=10.0, step=0.5)
        
        with col2:
            estoque = st.number_input("Quantidade Disponível *", min_value=1, value=10, step=1)
            horario_inicio = st.time_input("Início da Retirada *", value=datetime.strptime("18:00", "%H:%M").time())
            horario_fim = st.time_input("Fim da Retirada *", value=datetime.strptime("19:00", "%H:%M").time())
        
        descricao = st.text_area("Descrição", 
            placeholder="Descreva o que pode vir na caixa surpresa...")
        
        if st.form_submit_button("🚀 Publicar Oferta", use_container_width=True):
            if titulo and preco_venda < preco_original:
                oferta_id = db.criar_oferta(
                    estabelecimento_id=est_id,
                    titulo=titulo,
                    descricao=descricao,
                    categoria=categoria,
                    preco_original=preco_original,
                    preco_venda=preco_venda,
                    estoque=estoque,
                    horario_inicio=horario_inicio.strftime("%H:%M"),
                    horario_fim=horario_fim.strftime("%H:%M")
                )
                
                if oferta_id:
                    st.success("✅ Oferta publicada com sucesso!")
                    st.balloons()
                else:
                    st.error("Erro ao criar oferta")
            else:
                st.error("Verifique os campos. Preço de venda deve ser menor que o original.")

def tela_pedidos_estabelecimento(est_id):
    st.title("📦 Pedidos Recebidos")
    
    pedidos = db.listar_pedidos_estabelecimento(est_id)
    
    if not pedidos:
        st.info("Nenhum pedido recebido ainda. Publique ofertas para começar!")
        return
    
    # Filtros
    status_filtro = st.multiselect(
        "Filtrar por status",
        ["reservado", "pago", "retirado", "cancelado"],
        default=["reservado", "pago"]
    )
    
    pedidos_filtrados = [p for p in pedidos if p['status'] in status_filtro]
    
    st.markdown(f"**{len(pedidos_filtrados)} pedidos**")
    
    for pedido in pedidos_filtrados:
        with st.expander(f"🎫 Pedido #{pedido['id']} - {pedido['oferta']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Cliente:** {pedido['cliente']}")
                st.markdown(f"**Telefone:** {pedido['telefone']}")
                st.markdown(f"**Oferta:** {pedido['oferta']}")
                st.markdown(f"**Valor:** R$ {pedido['valor']:.2f}")
                st.markdown(f"**Data:** {pedido['data']}")
            
            with col2:
                st.markdown(f"**Status:** {pedido['status'].upper()}")
                st.code(pedido['codigo'])
                st.caption("Código de retirada")

def tela_validar_retirada():
    st.title("✅ Validar Retirada")
    
    st.markdown("""
    Digite o código de retirada apresentado pelo cliente para confirmar a entrega.
    """)
    
    codigo = st.text_input("🔑 Código de Retirada", max_chars=8, placeholder="Ex: A1B2C3D4")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("✅ Validar e Confirmar Retirada", use_container_width=True):
            if codigo:
                resultado = db.validar_retirada(codigo.upper())
                
                if resultado['sucesso']:
                    st.success(resultado['mensagem'])
                    st.info(f"**Oferta:** {resultado['detalhes']['oferta']}")
                    st.balloons()
                else:
                    st.error(resultado['mensagem'])
            else:
                st.warning("Digite o código de retirada")

# ============= FLUXO PRINCIPAL =============
def main():
    if not st.session_state.logged_in:
        tela_login()
    else:
        if st.session_state.user['tipo'] == 'consumidor':
            area_consumidor()
        else:
            area_estabelecimento()

if __name__ == "__main__":
    main()