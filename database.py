import sqlite3
from datetime import datetime
import hashlib

class Database:
    def __init__(self, db_name='pega_ai.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Cria conexão com o banco"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def init_database(self):
        """Cria estrutura do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('consumidor', 'estabelecimento')) NOT NULL,
                telefone TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de estabelecimentos (extensão)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estabelecimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER UNIQUE NOT NULL,
                nome_fantasia TEXT NOT NULL,
                cnpj TEXT UNIQUE,
                endereco TEXT,
                latitude REAL,
                longitude REAL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de ofertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ofertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estabelecimento_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT,
                categoria TEXT,
                preco_original REAL NOT NULL,
                preco_venda REAL NOT NULL,
                estoque_inicial INTEGER NOT NULL,
                estoque_atual INTEGER NOT NULL,
                horario_retirada_inicio TEXT NOT NULL,
                horario_retirada_fim TEXT NOT NULL,
                status TEXT DEFAULT 'ativa' CHECK(status IN ('ativa', 'pausada', 'esgotada')),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (estabelecimento_id) REFERENCES estabelecimentos(id),
                CHECK (preco_venda < preco_original),
                CHECK (estoque_atual >= 0 AND estoque_atual <= estoque_inicial)
            )
        ''')
        
        # Tabela de pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumidor_id INTEGER NOT NULL,
                oferta_id INTEGER NOT NULL,
                quantidade INTEGER DEFAULT 1,
                valor_total REAL NOT NULL,
                codigo_retirada TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'reservado' CHECK(status IN ('reservado', 'pago', 'retirado', 'cancelado')),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retirado_em TIMESTAMP,
                FOREIGN KEY (consumidor_id) REFERENCES usuarios(id),
                FOREIGN KEY (oferta_id) REFERENCES ofertas(id)
            )
        ''')
        
        # Tabela de avaliações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER UNIQUE NOT NULL,
                nota INTEGER NOT NULL CHECK(nota >= 1 AND nota <= 5),
                comentario TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def hash_senha(self, senha):
        """Gera hash SHA256 da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def criar_usuario(self, nome, email, senha, tipo, telefone=None):
        """Cria um novo usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, tipo, telefone)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, email, self.hash_senha(senha), tipo, telefone))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def autenticar_usuario(self, email, senha):
        """Autentica usuário e retorna seus dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, nome, email, tipo
            FROM usuarios
            WHERE email = ? AND senha = ?
        ''', (email, self.hash_senha(senha)))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'nome': user[1],
                'email': user[2],
                'tipo': user[3]
            }
        return None
    
    def criar_estabelecimento(self, usuario_id, nome_fantasia, cnpj, endereco, latitude, longitude):
        """Cria perfil de estabelecimento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO estabelecimentos (usuario_id, nome_fantasia, cnpj, endereco, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (usuario_id, nome_fantasia, cnpj, endereco, latitude, longitude))
            
            est_id = cursor.lastrowid
            conn.commit()
            return est_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def criar_oferta(self, estabelecimento_id, titulo, descricao, categoria, preco_original, 
                     preco_venda, estoque, horario_inicio, horario_fim):
        """Cria uma nova oferta"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ofertas (estabelecimento_id, titulo, descricao, categoria, preco_original, 
                                preco_venda, estoque_inicial, estoque_atual, 
                                horario_retirada_inicio, horario_retirada_fim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (estabelecimento_id, titulo, descricao, categoria, preco_original, 
              preco_venda, estoque, estoque, horario_inicio, horario_fim))
        
        oferta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return oferta_id
    
    def listar_ofertas_ativas(self):
        """Lista todas ofertas ativas com estoque"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.id, o.titulo, o.descricao, o.categoria, o.preco_original, o.preco_venda,
                   o.estoque_atual, o.horario_retirada_inicio, o.horario_retirada_fim,
                   e.nome_fantasia, e.endereco, e.latitude, e.longitude
            FROM ofertas o
            JOIN estabelecimentos e ON o.estabelecimento_id = e.id
            WHERE o.status = 'ativa' AND o.estoque_atual > 0
            ORDER BY o.criado_em DESC
        ''')
        
        ofertas = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': o[0], 'titulo': o[1], 'descricao': o[2], 'categoria': o[3],
                'preco_original': o[4], 'preco_venda': o[5], 'estoque': o[6],
                'horario_inicio': o[7], 'horario_fim': o[8],
                'estabelecimento': o[9], 'endereco': o[10],
                'latitude': o[11], 'longitude': o[12]
            }
            for o in ofertas
        ]
    
    def criar_pedido(self, consumidor_id, oferta_id, quantidade=1):
        """Cria um pedido e atualiza estoque"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Buscar preço e verificar estoque
        cursor.execute('SELECT preco_venda, estoque_atual FROM ofertas WHERE id = ?', (oferta_id,))
        oferta = cursor.fetchone()
        
        if not oferta or oferta[1] < quantidade:
            conn.close()
            return None
        
        valor_total = oferta[0] * quantidade
        codigo_retirada = hashlib.md5(f"{consumidor_id}{oferta_id}{datetime.now()}".encode()).hexdigest()[:8].upper()
        
        # Criar pedido
        cursor.execute('''
            INSERT INTO pedidos (consumidor_id, oferta_id, quantidade, valor_total, codigo_retirada)
            VALUES (?, ?, ?, ?, ?)
        ''', (consumidor_id, oferta_id, quantidade, valor_total, codigo_retirada))
        
        pedido_id = cursor.lastrowid
        
        # Atualizar estoque
        cursor.execute('''
            UPDATE ofertas 
            SET estoque_atual = estoque_atual - ?
            WHERE id = ?
        ''', (quantidade, oferta_id))
        
        conn.commit()
        conn.close()
        
        return {'id': pedido_id, 'codigo_retirada': codigo_retirada, 'valor_total': valor_total}
    
    def validar_retirada(self, codigo_retirada):
        """Valida código de retirada e marca como retirado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.status, o.titulo, e.nome_fantasia
            FROM pedidos p
            JOIN ofertas o ON p.oferta_id = o.id
            JOIN estabelecimentos e ON o.estabelecimento_id = e.id
            WHERE p.codigo_retirada = ?
        ''', (codigo_retirada,))
        
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return {'sucesso': False, 'mensagem': 'Código inválido'}
        
        if pedido[1] == 'retirado':
            conn.close()
            return {'sucesso': False, 'mensagem': 'Pedido já foi retirado'}
        
        if pedido[1] == 'cancelado':
            conn.close()
            return {'sucesso': False, 'mensagem': 'Pedido cancelado'}
        
        # Atualizar status
        cursor.execute('''
            UPDATE pedidos 
            SET status = 'retirado', retirado_em = CURRENT_TIMESTAMP
            WHERE codigo_retirada = ?
        ''', (codigo_retirada,))
        
        conn.commit()
        conn.close()
        
        return {
            'sucesso': True,
            'mensagem': f'Pedido retirado com sucesso!',
            'detalhes': {
                'oferta': pedido[2],
                'estabelecimento': pedido[3]
            }
        }
    
    def listar_pedidos_consumidor(self, consumidor_id):
        """Lista pedidos de um consumidor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.codigo_retirada, p.valor_total, p.status, p.criado_em,
                   o.titulo, e.nome_fantasia, e.endereco,
                   o.horario_retirada_inicio, o.horario_retirada_fim
            FROM pedidos p
            JOIN ofertas o ON p.oferta_id = o.id
            JOIN estabelecimentos e ON o.estabelecimento_id = e.id
            WHERE p.consumidor_id = ?
            ORDER BY p.criado_em DESC
        ''', (consumidor_id,))
        
        pedidos = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': p[0], 'codigo': p[1], 'valor': p[2], 'status': p[3],
                'data': p[4], 'oferta': p[5], 'estabelecimento': p[6],
                'endereco': p[7], 'horario_inicio': p[8], 'horario_fim': p[9]
            }
            for p in pedidos
        ]
    
    def get_estabelecimento_id(self, usuario_id):
        """Retorna ID do estabelecimento pelo usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM estabelecimentos WHERE usuario_id = ?', (usuario_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def listar_pedidos_estabelecimento(self, estabelecimento_id):
        """Lista pedidos de um estabelecimento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.codigo_retirada, p.valor_total, p.status, p.criado_em,
                   o.titulo, u.nome, u.telefone
            FROM pedidos p
            JOIN ofertas o ON p.oferta_id = o.id
            JOIN usuarios u ON p.consumidor_id = u.id
            WHERE o.estabelecimento_id = ?
            ORDER BY p.criado_em DESC
        ''', (estabelecimento_id,))
        
        pedidos = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': p[0], 'codigo': p[1], 'valor': p[2], 'status': p[3],
                'data': p[4], 'oferta': p[5], 'cliente': p[6], 'telefone': p[7]
            }
            for p in pedidos
        ]
