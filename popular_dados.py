import random
from datetime import datetime, timedelta
from database import Database

# Instalar faker: pip install faker
try:
    from faker import Faker
    fake = Faker('pt_BR')
except ImportError:
    print("⚠️  Instale o Faker: pip install faker")
    exit(1)

def popular_banco_dados():
    """Popula o banco com dados realistas para demonstração"""
    
    db = Database()
    print("🚀 Iniciando população do banco de dados...")
    
    # Dados para ofertas
    categorias = ['Padaria', 'Restaurante', 'Hortifrúti', 'Confeitaria', 'Mercado', 'Pizzaria']
    
    titulos_por_categoria = {
        'Padaria': ['Cesta de Pães Artesanais', 'Surpresa da Padaria', 'Mix de Pães e Bolos'],
        'Restaurante': ['Refeição Completa', 'Prato do Dia', 'Combo Executivo'],
        'Hortifrúti': ['Cesta de Frutas', 'Legumes Frescos', 'Mix Orgânico'],
        'Confeitaria': ['Doces Variados', 'Bolos e Tortas', 'Surpresa Doce'],
        'Mercado': ['Cesta Básica Mini', 'Produtos Frescos', 'Surpresa do Mercado'],
        'Pizzaria': ['Pizza Surpresa', 'Combo Pizza', 'Fatias Variadas']
    }
    
    # Coordenadas de São Paulo (diferentes bairros)
    coords_sp = [
        (-23.550520, -46.633308, 'Centro - Sé'),
        (-23.561414, -46.656011, 'Av. Paulista'),
        (-23.587416, -46.682426, 'Pinheiros'),
        (-23.574573, -46.645235, 'Jardins'),
        (-23.533773, -46.625290, 'Santana'),
        (-23.596593, -46.688034, 'Vila Madalena'),
        (-23.652221, -46.654659, 'Jabaquara'),
        (-23.519614, -46.618045, 'Tucuruvi'),
        (-23.600785, -46.663929, 'Vila Mariana'),
        (-23.545422, -46.639314, 'Bela Vista')
    ]
    
    usuarios_estabelecimentos = []
    usuarios_consumidores = []
    
    # 1. Criar 10 estabelecimentos
    print("\n📍 Criando estabelecimentos...")
    for i, (lat, lon, bairro) in enumerate(coords_sp):
        categoria = categorias[i % len(categorias)]
        nome_fantasia = f"{categoria} {fake.last_name()}"
        
        # Criar usuário do estabelecimento
        user_id = db.criar_usuario(
            nome=f"Admin {nome_fantasia}",
            email=f"estabelecimento{i+1}@pegaai.com",
            senha="senha123",  # Senha padrão para demo
            tipo="estabelecimento",
            telefone=fake.phone_number()
        )
        
        if user_id:
            # Criar perfil do estabelecimento
            est_id = db.criar_estabelecimento(
                usuario_id=user_id,
                nome_fantasia=nome_fantasia,
                cnpj=fake.cnpj(),
                endereco=f"{fake.street_name()}, {random.randint(10, 999)} - {bairro}, São Paulo - SP",
                latitude=lat,
                longitude=lon
            )
            
            if est_id:
                usuarios_estabelecimentos.append((user_id, est_id, categoria))
                print(f"  ✅ {nome_fantasia} ({bairro})")
    
    # 2. Criar 50 consumidores
    print("\n👥 Criando consumidores...")
    for i in range(50):
        user_id = db.criar_usuario(
            nome=fake.name(),
            email=f"consumidor{i+1}@email.com",
            senha="senha123",
            tipo="consumidor",
            telefone=fake.phone_number()
        )
        
        if user_id:
            usuarios_consumidores.append(user_id)
    
    print(f"  ✅ {len(usuarios_consumidores)} consumidores criados")
    
    # 3. Criar 30-40 ofertas distribuídas
    print("\n📦 Criando ofertas...")
    total_ofertas = 0
    
    for user_id, est_id, categoria in usuarios_estabelecimentos:
        # Cada estabelecimento cria 3-5 ofertas
        num_ofertas = random.randint(3, 5)
        
        for _ in range(num_ofertas):
            titulo = random.choice(titulos_por_categoria[categoria])
            preco_original = round(random.uniform(20, 60), 2)
            preco_venda = round(preco_original * random.uniform(0.25, 0.40), 2)  # 60-75% desconto
            
            descricoes = [
                f"Deliciosos produtos frescos do dia. Valor estimado de R$ {preco_original:.2f} por apenas R$ {preco_venda:.2f}!",
                f"Aproveite nossa seleção especial com até 70% de desconto. Uma surpresa deliciosa te aguarda!",
                f"Salve comida de qualidade e economize! Produtos frescos com grande desconto.",
                f"Caixa surpresa recheada de {categoria.lower()}. Qualidade garantida!"
            ]
            
            horarios = [
                ('17:00', '18:00'),
                ('18:00', '19:00'),
                ('19:00', '20:00'),
                ('20:00', '21:00')
            ]
            
            horario = random.choice(horarios)
            
            db.criar_oferta(
                estabelecimento_id=est_id,
                titulo=titulo,
                descricao=random.choice(descricoes),
                categoria=categoria,
                preco_original=preco_original,
                preco_venda=preco_venda,
                estoque=random.randint(5, 15),
                horario_inicio=horario[0],
                horario_fim=horario[1]
            )
            
            total_ofertas += 1
    
    print(f"  ✅ {total_ofertas} ofertas criadas")
    
    # 4. Criar 80-100 pedidos (simulando histórico)
    print("\n🛒 Criando pedidos (simulando histórico)...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar IDs de ofertas existentes
    cursor.execute('SELECT id FROM ofertas')
    ofertas_ids = [row[0] for row in cursor.fetchall()]
    
    total_pedidos = 0
    status_opcoes = [
        ('reservado', 0.15),   # 15% reservados
        ('pago', 0.10),        # 10% pagos (não retirados ainda)
        ('retirado', 0.70),    # 70% retirados (sucesso)
        ('cancelado', 0.05)    # 5% cancelados
    ]
    
    for _ in range(random.randint(80, 100)):
        consumidor_id = random.choice(usuarios_consumidores)
        oferta_id = random.choice(ofertas_ids)
        
        # Não decrementar estoque (já foi feito na criação)
        # Este é histórico simulado
        
        # Selecionar status baseado em probabilidades
        rand = random.random()
        cumulative = 0
        status_escolhido = 'reservado'
        
        for status, prob in status_opcoes:
            cumulative += prob
            if rand <= cumulative:
                status_escolhido = status
                break
        
        # Buscar preço
        cursor.execute('SELECT preco_venda FROM ofertas WHERE id = ?', (oferta_id,))
        preco = cursor.fetchone()[0]
        
        # Gerar código único
        codigo = fake.uuid4()[:8].upper()
        
        # Data variando nos últimos 30 dias
        dias_atras = random.randint(0, 30)
        data_criacao = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO pedidos (consumidor_id, oferta_id, quantidade, valor_total, 
                               codigo_retirada, status, criado_em)
            VALUES (?, ?, 1, ?, ?, ?, ?)
        ''', (consumidor_id, oferta_id, preco, codigo, status_escolhido, data_criacao))
        
        total_pedidos += 1
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ {total_pedidos} pedidos criados")
    
    # 5. Criar algumas avaliações
    print("\n⭐ Criando avaliações...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar pedidos retirados
    cursor.execute('SELECT id FROM pedidos WHERE status = "retirado" LIMIT 30')
    pedidos_retirados = [row[0] for row in cursor.fetchall()]
    
    comentarios = [
        "Excelente! Comida fresca e deliciosa.",
        "Adorei a variedade. Voltarei com certeza!",
        "Ótimo custo-benefício. Recomendo!",
        "Produtos de qualidade. Vale muito a pena!",
        "Surpreendeu positivamente. Muita coisa boa!",
        "Bom, mas esperava um pouco mais.",
        "Razoável. Atendeu as expectativas.",
        None  # Alguns sem comentário
    ]
    
    total_avaliacoes = 0
    for pedido_id in pedidos_retirados[:20]:  # Avaliar 20 pedidos
        nota = random.choices([3, 4, 5], weights=[0.1, 0.3, 0.6])[0]  # Mais notas altas
        comentario = random.choice(comentarios)
        
        try:
            cursor.execute('''
                INSERT INTO avaliacoes (pedido_id, nota, comentario)
                VALUES (?, ?, ?)
            ''', (pedido_id, nota, comentario))
            total_avaliacoes += 1
        except:
            pass  # Ignora duplicatas
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ {total_avaliacoes} avaliações criadas")
    
    print("\n" + "="*60)
    print("✅ BANCO POPULADO COM SUCESSO!")
    print("="*60)
    print(f"""
📊 Resumo:
   • {len(usuarios_estabelecimentos)} estabelecimentos
   • {len(usuarios_consumidores)} consumidores
   • {total_ofertas} ofertas ativas
   • {total_pedidos} pedidos (histórico simulado)
   • {total_avaliacoes} avaliações

🔐 Credenciais de Teste:
   Estabelecimento: estabelecimento1@pegaai.com / senha123
   Consumidor: consumidor1@email.com / senha123
    """)

if __name__ == "__main__":
    popular_banco_dados()
