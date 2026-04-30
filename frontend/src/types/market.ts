export interface EnhancedMarket {
  id: string;
  condition_id: string;
  question: string;
  description: string | null;
  category: string | null;
  slug: string | null;
  yes_price: number | null;
  no_price: number | null;
  volume: number | null;
  liquidity: number | null;
  end_date: string | null;
  is_active: boolean;
  resolved: boolean;
  last_fetched_at: string;
  edge_potential: number | null;
  liquidity_score: number | null;
  composite_score: number | null;
  research_status: 'researched' | 'stale' | null;
  last_researched_at: string | null;
  user_has_position: boolean;
  position_side: string | null;
  spread: number | null;
  hours_to_resolution: number | null;
}
