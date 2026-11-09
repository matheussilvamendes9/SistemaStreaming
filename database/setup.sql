USE streaming_data;

-- 1. Cria a tabela de avaliações
CREATE TABLE imdb_ratings (
    tconst VARCHAR(15) PRIMARY KEY,
    averageRating DECIMAL(3,1), -- Formato decimal para notas (ex: 8.5)
    numVotes INT                -- Número inteiro para a quantidade de votos
);

-- 2. Importa os dados do arquivo TSV
LOAD DATA INFILE '/tmp/title.ratings.tsv'
INTO TABLE imdb_ratings
CHARACTER SET utf8mb4
FIELDS TERMINATED BY '\t'
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(tconst, averageRating, numVotes);