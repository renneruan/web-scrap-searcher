create DATABASE indice;

use indice;

create table urls(
    idurl int not null auto_increment,
    url varchar(512) not null,
    PRIMARY KEY (idurl)
);

create index idx_urls_url on urls (url);

create table palavras (
    idpalavra int not null auto_increment,
    palavra varchar(200) not null,
    primary key (idpalavra)
);

create index idx_palavras_palavra on palavras (palavra);

create table palavra_localizacao (
    idpalavra_localizacao int not null auto_increment,
    idurl int not null,
    idpalavra int not null,
    localizacao int,
    constraint pk_idpalavra_localizacao primary key (idpalavra_localizacao),
    constraint fk_palavra_localizacao_idurl foreign key (idurl) references urls (idurl),
    constraint fk_palavra_localizacao_idpalavra foreign key (idpalavra) references palavras (idpalavra)
);

create index idx_palavra_localizacao_idpalavra on palavra_localizacao (idpalavra);

ALTER DATABASE indice CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

ALTER TABLE
    palavras CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE
    palavras
modify
    column palavra VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;