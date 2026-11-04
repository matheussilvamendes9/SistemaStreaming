-- Banco operacional do SistemaStreaming
-- Requer MySQL 8.0.16+ (CHECK) e tabelas InnoDB.
-- O schema streaming_db deve existir antes da execucao.
-- Execute apenas em um banco novo ou cuja estrutura ja seja compativel.

USE streaming_db;

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuario_email UNIQUE (email),
    CONSTRAINT ck_usuario_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0),
    CONSTRAINT ck_usuario_email CHECK (CHAR_LENGTH(TRIM(email)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS plano (
    id_plano INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    CONSTRAINT uq_plano_nome UNIQUE (nome),
    CONSTRAINT ck_plano_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0),
    CONSTRAINT ck_plano_valor CHECK (valor > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS conteudo (
    id_conteudo INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    tipo ENUM('filme', 'serie') NOT NULL,
    ano_lancamento SMALLINT UNSIGNED NOT NULL,
    duracao_minutos INT UNSIGNED NULL,
    CONSTRAINT ck_conteudo_titulo CHECK (CHAR_LENGTH(TRIM(titulo)) > 0),
    CONSTRAINT ck_conteudo_ano CHECK (ano_lancamento BETWEEN 1888 AND 2100),
    CONSTRAINT ck_conteudo_duracao CHECK (
        (tipo = 'filme' AND duracao_minutos IS NOT NULL AND duracao_minutos > 0)
        OR (tipo = 'serie' AND duracao_minutos IS NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS genero (
    id_genero INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL,
    CONSTRAINT uq_genero_nome UNIQUE (nome),
    CONSTRAINT ck_genero_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS assinatura (
    id_assinatura INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT UNSIGNED NOT NULL,
    id_plano INT UNSIGNED NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    data_inicio DATE NOT NULL,
    data_termino DATE NULL,
    status ENUM('ativa', 'cancelada', 'expirada') NOT NULL DEFAULT 'ativa',
    -- UNIQUE permite varios NULLs, mas apenas uma linha ativa por usuario.
    -- Coluna comum mantida pelos triggers trg_assinatura_bi/bu (nao pode ser
    -- GENERATED STORED: o MySQL nao aceita FK com CASCADE na coluna-base).
    usuario_ativo INT UNSIGNED NULL,
    CONSTRAINT uq_assinatura_usuario_ativo UNIQUE (usuario_ativo),
    CONSTRAINT ck_assinatura_valor CHECK (valor > 0),
    CONSTRAINT ck_assinatura_datas CHECK (
        data_termino IS NULL OR data_termino >= data_inicio
    ),
    CONSTRAINT ck_assinatura_status CHECK (
        (status = 'ativa' AND data_termino IS NULL)
        OR (status <> 'ativa' AND data_termino IS NOT NULL)
    ),
    -- ON UPDATE RESTRICT: acoes em cascata nao disparam triggers, e alterar
    -- id_usuario deixaria usuario_ativo desatualizado.
    CONSTRAINT fk_assinatura_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_assinatura_plano FOREIGN KEY (id_plano)
        REFERENCES plano (id_plano) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS episodio (
    id_episodio INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_serie INT UNSIGNED NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    temporada SMALLINT UNSIGNED NOT NULL,
    episodio SMALLINT UNSIGNED NOT NULL,
    duracao_minutos INT UNSIGNED NOT NULL,
    CONSTRAINT uq_episodio_serie_temporada_numero UNIQUE (id_serie, temporada, episodio),
    -- Permite FK composta do historico, assegurando episodio da serie correta.
    CONSTRAINT uq_episodio_id_serie UNIQUE (id_episodio, id_serie),
    CONSTRAINT ck_episodio_titulo CHECK (CHAR_LENGTH(TRIM(titulo)) > 0),
    CONSTRAINT ck_episodio_temporada CHECK (temporada > 0),
    CONSTRAINT ck_episodio_numero CHECK (episodio > 0),
    CONSTRAINT ck_episodio_duracao CHECK (duracao_minutos > 0),
    CONSTRAINT fk_episodio_serie FOREIGN KEY (id_serie)
        REFERENCES conteudo (id_conteudo) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS conteudo_genero (
    id_conteudo INT UNSIGNED NOT NULL,
    id_genero INT UNSIGNED NOT NULL,
    PRIMARY KEY (id_conteudo, id_genero),
    CONSTRAINT fk_conteudo_genero_conteudo FOREIGN KEY (id_conteudo)
        REFERENCES conteudo (id_conteudo) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_conteudo_genero_genero FOREIGN KEY (id_genero)
        REFERENCES genero (id_genero) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS historico_reproducao (
    id_reproducao INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT UNSIGNED NOT NULL,
    id_conteudo INT UNSIGNED NOT NULL,
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    progresso_minutos DECIMAL(10,2) NOT NULL DEFAULT 0,
    id_episodio INT UNSIGNED NULL,
    CONSTRAINT ck_historico_progresso CHECK (progresso_minutos >= 0),
    CONSTRAINT fk_historico_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_historico_conteudo FOREIGN KEY (id_conteudo)
        REFERENCES conteudo (id_conteudo) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_historico_episodio_serie FOREIGN KEY (id_episodio, id_conteudo)
        REFERENCES episodio (id_episodio, id_serie)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_historico_ultima_atividade (id_usuario, data_hora, id_reproducao),
    INDEX idx_historico_conteudo (id_conteudo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Triggers: episodio somente em serie; historico de filme sem episodio,
-- historico de serie obrigatoriamente com episodio; assinatura ativa unica.
-- Os gatilhos sao recriados para permitir reexecutar este script.
DROP TRIGGER IF EXISTS trg_episodio_bi;
DROP TRIGGER IF EXISTS trg_episodio_bu;
DROP TRIGGER IF EXISTS trg_historico_bi;
DROP TRIGGER IF EXISTS trg_historico_bu;
DROP TRIGGER IF EXISTS trg_conteudo_bu;
DROP TRIGGER IF EXISTS trg_assinatura_bi;
DROP TRIGGER IF EXISTS trg_assinatura_bu;

DELIMITER $$

CREATE TRIGGER trg_episodio_bi BEFORE INSERT ON episodio
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM conteudo WHERE id_conteudo = NEW.id_serie AND tipo = 'serie'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Episodio deve pertencer a um conteudo do tipo serie';
    END IF;
END$$

CREATE TRIGGER trg_episodio_bu BEFORE UPDATE ON episodio
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM conteudo WHERE id_conteudo = NEW.id_serie AND tipo = 'serie'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Episodio deve pertencer a um conteudo do tipo serie';
    END IF;
END$$

CREATE TRIGGER trg_historico_bi BEFORE INSERT ON historico_reproducao
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM conteudo
        WHERE id_conteudo = NEW.id_conteudo
          AND ((tipo = 'filme' AND NEW.id_episodio IS NULL)
            OR (tipo = 'serie' AND NEW.id_episodio IS NOT NULL))
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Historico invalido: filme sem episodio ou serie com episodio obrigatorio';
    END IF;
END$$

CREATE TRIGGER trg_historico_bu BEFORE UPDATE ON historico_reproducao
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM conteudo
        WHERE id_conteudo = NEW.id_conteudo
          AND ((tipo = 'filme' AND NEW.id_episodio IS NULL)
            OR (tipo = 'serie' AND NEW.id_episodio IS NOT NULL))
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Historico invalido: filme sem episodio ou serie com episodio obrigatorio';
    END IF;
END$$

CREATE TRIGGER trg_conteudo_bu BEFORE UPDATE ON conteudo
FOR EACH ROW
BEGIN
    IF NEW.tipo <> OLD.tipo AND (
        EXISTS (SELECT 1 FROM episodio WHERE id_serie = OLD.id_conteudo)
        OR EXISTS (SELECT 1 FROM historico_reproducao WHERE id_conteudo = OLD.id_conteudo)
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nao e permitido alterar tipo de conteudo com episodios ou historico';
    END IF;
END$$

-- Mantem usuario_ativo: id do usuario quando ativa, NULL caso contrario (RN04).
CREATE TRIGGER trg_assinatura_bi BEFORE INSERT ON assinatura
FOR EACH ROW
BEGIN
    SET NEW.usuario_ativo = IF(NEW.status = 'ativa', NEW.id_usuario, NULL);
END$$

CREATE TRIGGER trg_assinatura_bu BEFORE UPDATE ON assinatura
FOR EACH ROW
BEGIN
    SET NEW.usuario_ativo = IF(NEW.status = 'ativa', NEW.id_usuario, NULL);
END$$

DELIMITER ;

-- =====================================================
-- CADASTRO DOS PLANOS INICIAIS
-- =====================================================

INSERT INTO plano (nome, valor)
VALUES
    ('basico', 20.00),
    ('padrao', 35.00),
    ('premium', 50.00)
ON DUPLICATE KEY UPDATE id_plano = id_plano;
