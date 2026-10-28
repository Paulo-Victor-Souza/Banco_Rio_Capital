-- Criar a base de dados
CREATE DATABASE BANCO;
GO

USE BANCO;
GO

-- Criar a tabela de contas (conforme mencionado no seu README)
CREATE TABLE dbo.CONTA (
    id INT IDENTITY(1,1) PRIMARY KEY,
    titular VARCHAR(100) NOT NULL,
    saldo DECIMAL(18, 2) NOT NULL DEFAULT 0.00
);
GO

-- (Opcional) Inserir dados de teste para demonstração
INSERT INTO dbo.CONTA (titular, saldo) VALUES ('João Silva', 1500.00);
INSERT INTO dbo.CONTA (titular, saldo) VALUES ('Maria Santos', 3250.50);
GO