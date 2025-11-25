import unittest
import os
import sqlite3
import hashlib
from database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary database for testing"""
        self.test_db = 'test_pega_ai.db'
        self.db = Database(self.test_db)

    def tearDown(self):
        """Clean up the temporary database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_criar_usuario_e_autenticar(self):
        """Test user creation and authentication with salt"""
        # Create user
        user_id = self.db.criar_usuario(
            "Teste User", "teste@email.com", "senha123", "consumidor"
        )
        self.assertIsNotNone(user_id)

        # Authenticate with correct password
        user = self.db.autenticar_usuario("teste@email.com", "senha123")
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], "teste@email.com")
        self.assertEqual(user['nome'], "Teste User")

        # Authenticate with wrong password
        user_wrong = self.db.autenticar_usuario("teste@email.com", "wrongpass")
        self.assertIsNone(user_wrong)

    def test_autenticar_usuario_legado(self):
        """Test authentication for legacy users (unsalted password)"""
        # Manually insert a legacy user
        conn = self.db.get_connection()
        cursor = conn.cursor()
        legacy_pass = hashlib.sha256("senha_antiga".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, tipo)
            VALUES (?, ?, ?, ?)
        ''', ("Legacy User", "legacy@email.com", legacy_pass, "consumidor"))
        conn.commit()
        conn.close()

        # Try to authenticate
        user = self.db.autenticar_usuario("legacy@email.com", "senha_antiga")
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], "legacy@email.com")

    def test_criar_estabelecimento_e_oferta(self):
        """Test establishment and offer creation"""
        # Create establishment user
        user_id = self.db.criar_usuario(
            "Est User", "est@email.com", "senha123", "estabelecimento"
        )
        est_id = self.db.criar_estabelecimento(
            user_id, "Padaria Teste", "12345678000199",
            "Rua Teste, 123", -23.55, -46.63
        )
        self.assertIsNotNone(est_id)

        # Create offer
        oferta_id = self.db.criar_oferta(
            est_id, "Pão Fresco", "Delicioso", "Padaria",
            20.0, 10.0, 5, "18:00", "19:00"
        )
        self.assertIsNotNone(oferta_id)

        # List offers
        ofertas = self.db.listar_ofertas_ativas()
        self.assertEqual(len(ofertas), 1)
        self.assertEqual(ofertas[0]['titulo'], "Pão Fresco")

    def test_fluxo_pedido(self):
        """Test order creation, stock update, and cancellation"""
        # Setup: Consumer, Establishment, Offer
        cons_id = self.db.criar_usuario("Consumidor", "cons@email.com", "123", "consumidor")
        est_user_id = self.db.criar_usuario("Estabel", "est2@email.com", "123", "estabelecimento")
        est_id = self.db.criar_estabelecimento(est_user_id, "Restaurante", "111", "End", 0, 0)

        oferta_id = self.db.criar_oferta(
            est_id, "Comida", "Boa", "Restaurante",
            50.0, 25.0, 2, "12:00", "13:00"
        )

        # 1. Create Order
        pedido = self.db.criar_pedido(cons_id, oferta_id, 1)
        self.assertIsNotNone(pedido)

        # Check stock reduced
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT estoque_atual FROM ofertas WHERE id = ?', (oferta_id,))
        estoque = cursor.fetchone()[0]
        self.assertEqual(estoque, 1)
        conn.close()

        # 2. Cancel Order
        res = self.db.cancelar_pedido(pedido['id'])
        self.assertTrue(res['sucesso'])

        # Check stock returned
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT estoque_atual FROM ofertas WHERE id = ?', (oferta_id,))
        estoque = cursor.fetchone()[0]
        self.assertEqual(estoque, 2)
        conn.close()

if __name__ == '__main__':
    unittest.main()
