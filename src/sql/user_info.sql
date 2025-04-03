SELECT 
        DISTINCT
        a.user_id AS id_cliente,
        a.user_name AS nome_cliente,
        SAFE_CAST(
        DATE_DIFF(
        CURRENT_DATE(),
        SAFE.PARSE_DATE('%d/%m/%Y', COALESCE(c.birthday, e.birthday)),
        DAY
        ) / 365.26 AS INT
        ) AS idade,
        b.status
    FROM `infinitepay-production.metrics_amlft.bets_pix_transfers` a
    INNER JOIN `infinitepay-production.maindb.users` b
        ON b.id = a.user_id
    LEFT JOIN (
    SELECT DISTINCT me.user_id, re.birthday
    FROM `infinitepay-production.maindb.merchants` me
    INNER JOIN `infinitepay-production.maindb.legal_representatives` re
    ON me.legal_representative_id = re.id
        ) c
        ON c.user_id = a.user_id
    LEFT JOIN (
    SELECT DISTINCT user_id, birthday
    FROM `infinitepay-production.maindb.cardholders`
        ) e
    ON e.user_id = a.user_id
    WHERE a.user_id = {id_client}
    ORDER BY nome_cliente