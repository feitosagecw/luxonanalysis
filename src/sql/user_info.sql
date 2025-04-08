SELECT 
        DISTINCT
        a.id AS id_cliente,
        e.name Nome,
        SAFE_CAST(DATE_DIFF(CURRENT_DATE(),SAFE.PARSE_DATE('%d/%m/%Y', COALESCE(b.birthday, e.birthday)),DAY) / 365.26 AS INT)AS idade,
        a.status,
        CASE
            WHEN b.document_type = "cnpj" THEN "Merchant Pessoa Jurídica"
            WHEN b.document_type = "cpf" THEN "Merchant Pessoa Física"
            ELSE "Cardholder"
        END AS Role_Type,
        COALESCE(b.business_category,"Não Informado") categoria_negocio, 
        COALESCE(b.document_number,b.cpf,e.cpf,"00000000000") document_number,
        CAST(e.created_at AS DATE) as created_at_ch,
        CAST(b.created_at AS DATE) as created_at_me
    FROM `infinitepay-production.maindb.users` a
    LEFT JOIN (
    SELECT DISTINCT me.user_id, me.document_type, me. business_category, me.document_number, me.created_at, re.birthday, re.name,re.cpf
    FROM `infinitepay-production.maindb.merchants` me
    INNER JOIN `infinitepay-production.maindb.legal_representatives` re
    ON me.legal_representative_id = re.id
        ) b
        ON b.user_id = a.id
    LEFT JOIN (
    SELECT DISTINCT user_id, name, birthday, created_at, cpf
    FROM `infinitepay-production.maindb.cardholders`
        ) e
    ON e.user_id = a.id
    WHERE a.id = {id_client}