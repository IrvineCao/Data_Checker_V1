WITH campaign_count AS (
    SELECT COUNT(DISTINCT CONCAT(camp.storefront_id, '-', MONTH(perf.created_datetime))) as cnt
    FROM ads_ops_ads_campaigns camp
    INNER JOIN ads_ops_ads_campaigns_performance perf ON camp.id = perf.ads_campaign_id
    WHERE camp.storefront_id IN :storefront_ids AND MONTH(perf.created_datetime) IN :months
),
object_count AS (
    SELECT COUNT(DISTINCT CONCAT(obj.storefront_id, '-', MONTH(perf.created_datetime))) as cnt
    FROM ads_ops_ads_objects obj
    INNER JOIN ads_ops_ads_objects_performance perf ON obj.id = perf.ads_object_id
    WHERE obj.storefront_id IN :storefront_ids AND MONTH(perf.created_datetime) IN :months
),
placement_count AS (
    SELECT COUNT(DISTINCT CONCAT(pl.storefront_id, '-', MONTH(perf.created_datetime))) as cnt
    FROM ads_ops_ads_placements pl
    INNER JOIN ads_ops_ads_placements_performance perf ON pl.id = perf.ads_placement_id
    WHERE pl.storefront_id IN :storefront_ids AND MONTH(perf.created_datetime) IN :months
        AND perf.timing = 'daily'
)
SELECT 
    CASE 
        WHEN :aggregate_levels = true THEN (
            SELECT COUNT(DISTINCT CONCAT(storefront_id, '-', month))
            FROM (
                SELECT storefront_id, month FROM (SELECT 1) dummy
                CROSS JOIN (SELECT UNNEST(:storefront_ids) as storefront_id) sf
                CROSS JOIN (SELECT UNNEST(:months) as month) mn
            ) combinations
        )
        ELSE (
            COALESCE((SELECT cnt FROM campaign_count), 0) +
            COALESCE((SELECT cnt FROM object_count), 0) +
            COALESCE((SELECT cnt FROM placement_count), 0)
        )
    END as total_count