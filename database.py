import sqlite3
from datetime import datetime
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Union

class Database:
    def __init__(self, db_name: str = 'pega_ai.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Cria conexão com o banco"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def init_database(self) -> None:
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
        
        # Tabela de pagamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER UNIQUE NOT NULL,
                metodo TEXT CHECK(metodo IN ('pix', 'cartao', 'na_retirada')) NOT NULL,
                status TEXT DEFAULT 'pendente' CHECK(status IN ('pendente', 'aprovado', 'recusado', 'estornado')),
                gateway_id TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE
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
        
        # Índices de Performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ofertas_estabelecimento ON ofertas(estabelecimento_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedidos_consumidor ON pedidos(consumidor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedidos_oferta ON pedidos(oferta_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status)')

        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def hash_senha(self, senha: str, salt: Optional[str] = None) -> str:
        """Gera hash SHA256 da senha com salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((salt + senha).encode()).hexdigest()
        return f"{salt}${hash_obj}"
    
    def criar_usuario(self, nome: str, email: str, senha: str, tipo: str, telefone: Optional[str] = None) -> Optional[int]:
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
    
    def autenticar_usuario(self, email: str, senha: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário e retorna seus dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, nome, email, senha, tipo
            FROM usuarios
            WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            stored_hash = user[3]

            # Verificar se é hash legado (sem salt/delimitador $)
            if '$' not in stored_hash:
                if hashlib.sha256(senha.encode()).hexdigest() == stored_hash:
                    # Opcional: Atualizar senha para novo formato
                    return {
                        'id': user[0],
                        'nome': user[1],
                        'email': user[2],
                        'tipo': user[4]
                    }
            else:
                try:
                    salt = stored_hash.split('$')[0]
                    if self.hash_senha(senha, salt) == stored_hash:
                        return {
                            'id': user[0],
                            'nome': user[1],
                            'email': user[2],
                            'tipo': user[4]
                        }
                except (ValueError, IndexError):
                    pass

        return None
    
    def criar_estabelecimento(self, usuario_id: int, nome_fantasia: str, cnpj: str, endereco: str, latitude: float, longitude: float) -> Optional[int]:
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
    
    def criar_oferta(self, estabelecimento_id: int, titulo: str, descricao: str, categoria: str, preco_original: float,
                     preco_venda: float, estoque: int, horario_inicio: str, horario_fim: str) -> int:
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
    
    def listar_ofertas_ativas(self) -> List[Dict[str, Any]]:
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
    
    def criar_pedido(self, consumidor_id: int, oferta_id: int, quantidade: int = 1) -> Optional[Dict[str, Any]]:
        """Cria um pedido, atualiza estoque e registra pagamento (RF09 + RF10)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Buscar preço e verificar estoque
            cursor.execute('SELECT preco_venda, estoque_atual FROM ofertas WHERE id = ?', (oferta_id,))
            oferta = cursor.fetchone()
            
            if not oferta:
                conn.close()
                return None
            
            preco_unitario, estoque_disponivel = oferta
            
            # 2. Validar estoque
            if estoque_disponivel < quantidade:
                conn.close()
                return None
            
            # 3. Calcular valor total
            valor_total = preco_unitario * quantidade
            
            # 4. Gerar código único de retirada
            codigo_retirada = hashlib.md5(
                f"{consumidor_id}{oferta_id}{datetime.now()}{quantidade}".encode()
            ).hexdigest()[:8].upper()
            
            # 5. Criar pedido (status inicial: reservado)
            cursor.execute('''
                INSERT INTO pedidos (consumidor_id, oferta_id, quantidade, valor_total, codigo_retirada, status)
                VALUES (?, ?, ?, ?, ?, 'reservado')
            ''', (consumidor_id, oferta_id, quantidade, valor_total, codigo_retirada))
            
            pedido_id = cursor.lastrowid
            
            # 6. Criar pagamento (simulado como aprovado para demo)
            cursor.execute('''
                INSERT INTO pagamentos (pedido_id, metodo, status, gateway_id)
                VALUES (?, 'pix', 'aprovado', ?)
            ''', (pedido_id, f"SIM_{codigo_retirada}"))
            
            # 7. Atualizar status do pedido para "pago"
            cursor.execute('''
                UPDATE pedidos 
                SET status = 'pago'
                WHERE id = ?
            ''', (pedido_id,))
            
            # 8. Decrementar estoque (RNF07 - Confiabilidade)
            cursor.execute('''
                UPDATE ofertas 
                SET estoque_atual = estoque_atual - ?
                WHERE id = ? AND estoque_atual >= ?
            ''', (quantidade, oferta_id, quantidade))
            
            # 9. Verificar se o estoque foi realmente decrementado
            if cursor.rowcount == 0:
                conn.rollback()
                conn.close()
                return None
            
            conn.commit()
            conn.close()
            
            return {
                'id': pedido_id,
                'codigo_retirada': codigo_retirada,
                'valor_total': valor_total,
                'quantidade': quantidade
            }
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Erro ao criar pedido: {e}")
            return None
    
    def validar_retirada(self, codigo_retirada: str) -> Dict[str, Any]:
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
    
    def listar_pedidos_consumidor(self, consumidor_id: int) -> List[Dict[str, Any]]:
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
    
    def get_estabelecimento_id(self, usuario_id: int) -> Optional[int]:
        """Retorna ID do estabelecimento pelo usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM estabelecimentos WHERE usuario_id = ?', (usuario_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def listar_pedidos_estabelecimento(self, estabelecimento_id: int) -> List[Dict[str, Any]]:
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
    
    def cancelar_pedido(self, pedido_id: int, motivo: str = 'Cancelado pelo estabelecimento') -> Dict[str, Any]:
        """Cancela um pedido e devolve estoque (RF - Cancelamento/Devolução)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Buscar dados do pedido
        cursor.execute('''
            SELECT p.id, p.status, p.oferta_id, p.quantidade, pag.id as pagamento_id
            FROM pedidos p
            LEFT JOIN pagamentos pag ON p.id = pag.pedido_id
            WHERE p.id = ?
        ''', (pedido_id,))
        
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return {'sucesso': False, 'mensagem': 'Pedido não encontrado'}
        
        status_atual = pedido[1]
        oferta_id = pedido[2]
        quantidade = pedido[3]
        pagamento_id = pedido[4]
        
        # Só pode cancelar se for Reservado ou Pago
        if status_atual not in ['reservado', 'pago']:
            conn.close()
            return {'sucesso': False, 'mensagem': f'Pedido já está {status_atual}'}
        
        try:
            # 1. Atualizar status do pedido
            cursor.execute('''
                UPDATE pedidos 
                SET status = 'cancelado'
                WHERE id = ?
            ''', (pedido_id,))
            
            # 2. Devolver estoque
            cursor.execute('''
                UPDATE ofertas 
                SET estoque_atual = estoque_atual + ?
                WHERE id = ?
            ''', (quantidade, oferta_id))
            
            # 3. Estornar pagamento (se existir)
            if pagamento_id and status_atual == 'pago':
                cursor.execute('''
                    UPDATE pagamentos 
                    SET status = 'estornado'
                    WHERE id = ?
                ''', (pagamento_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'sucesso': True,
                'mensagem': 'Pedido cancelado com sucesso',
                'estoque_devolvido': quantidade,
                'pagamento_estornado': bool(pagamento_id and status_atual == 'pago')
            }
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return {'sucesso': False, 'mensagem': f'Erro ao cancelar: {str(e)}'}
