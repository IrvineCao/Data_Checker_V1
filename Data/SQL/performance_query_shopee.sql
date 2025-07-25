WITH campaign_performance AS (
    SELECT
        camp.storefront_id,
        'campaign' as level,
        MONTH(perf.created_datetime) as month,
        SUM(perf.impression) as impressions,
        SUM(perf.click) as clicks,
        SUM(perf.ads_gmv) as gmv,
        SUM(perf.cost) as expense,
        CASE 
            WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
            ELSE 0 
        END as roas
    FROM ads_ops_ads_campaigns camp
    INNER JOIN ads_ops_ads_campaigns_performance perf 
        ON camp.id = perf.ads_campaign_id
    WHERE camp.storefront_id IN :storefront_ids
        AND camp.tool_code IN ('SHP_PRODUCT_ADS','SHP_SHOP_ADS')
        AND camp.marketplace_code = 'shopee'
        AND MONTH(perf.created_datetime) IN :months
    GROUP BY camp.storefront_id, MONTH(perf.created_datetime)
), 

object_performance AS (
    SELECT
        obj.storefront_id,
        'object' as level,
        MONTH(perf.created_datetime) as month,
        SUM(perf.impression) as impressions,
        SUM(perf.click) as clicks,
        SUM(perf.ads_gmv) as gmv,
        SUM(perf.cost) as expense,
        CASE 
            WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
            ELSE 0 
        END as roas
    FROM ads_ops_ads_objects obj
    INNER JOIN ads_ops_ads_objects_performance perf 
        ON obj.id = perf.ads_object_id
    WHERE obj.storefront_id IN :storefront_ids
        AND obj.marketplace_code = 'shopee'
        AND obj.tool_code IN ('SHP_PRODUCT_ADS','SHP_SHOP_ADS')
        AND MONTH(perf.created_datetime) IN :months
    GROUP BY obj.storefront_id, MONTH(perf.created_datetime)
),

placement_performance AS (
    SELECT
        pl.storefront_id,
        'placement' as level,
        MONTH(perf.created_datetime) as month,
        SUM(perf.impression) as impressions,
        SUM(perf.click) as clicks,
        SUM(perf.ads_gmv) as gmv,
        SUM(perf.cost) as expense,
        CASE 
            WHEN SUM(perf.cost) > 0 THEN SUM(perf.ads_gmv) / SUM(perf.cost)
            ELSE 0 
        END as roas
    FROM ads_ops_ads_placements pl
    INNER JOIN ads_ops_ads_placements_performance perf 
        ON pl.id = perf.ads_placement_id
    WHERE pl.storefront_id IN :storefront_ids
        AND perf.timing = 'daily'
        AND pl.marketplace_code = 'shopee'
        AND pl.tool_code IN ('SHP_PRODUCT_ADS','SHP_SHOP_ADS')
        AND MONTH(perf.created_datetime) IN :months
    GROUP BY pl.storefront_id, MONTH(perf.created_datetime)
),

unified_performance AS (
    SELECT * FROM campaign_performance
    UNION ALL
    SELECT * FROM object_performance
    UNION ALL
    SELECT * FROM placement_performance
)

SELECT 
    storefront_id,
    CASE 
        WHEN :aggregate_levels = true THEN 'aggregated'
        ELSE level 
    END as level,
    month,
    CASE 
        WHEN :aggregate_levels = true THEN SUM(impressions)
        ELSE impressions 
    END as impressions,
    CASE 
        WHEN :aggregate_levels = true THEN SUM(clicks)
        ELSE clicks 
    END as clicks,
    CASE 
        WHEN :aggregate_levels = true THEN SUM(gmv)
        ELSE gmv 
    END as gmv,
    CASE 
        WHEN :aggregate_levels = true THEN SUM(expense)
        ELSE expense 
    END as expense,
    CASE 
        WHEN :aggregate_levels = true AND SUM(expense) > 0 THEN SUM(gmv) / SUM(expense)
        WHEN :aggregate_levels = false THEN roas
        ELSE 0 
    END as roas
FROM unified_performance
GROUP BY 
    storefront_id,
    month,
    CASE 
        WHEN :aggregate_levels = true THEN 'aggregated'
        ELSE level 
    END
ORDER BY storefront_id, month, level