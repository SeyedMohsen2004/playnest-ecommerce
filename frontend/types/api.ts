export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Category = {
  id: number;
  name: string;
  slug: string;
  parent: number | null;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Brand = {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductImage = {
  id: number;
  image: string;
  alt_text: string;
  is_main: boolean;
  created_at: string;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  description: string;
  short_description: string | null;
  sku: string;
  price: number;
  discount_price: number | null;
  final_price: number;
  stock: number;
  is_in_stock: boolean;
  age_group: "0_2" | "3_5" | "6_8" | "9_12" | "12_plus";
  gender: "unisex" | "boy" | "girl";
  is_active: boolean;
  is_featured: boolean;
  category: number | Category;
  category_detail?: Category | null;
  brand: number | Brand | null;
  brand_detail?: Brand | null;
  images?: ProductImage[];
  main_image?: ProductImage | null;
  average_rating?: number | string | null;
  review_count?: number;
  created_at: string;
  updated_at?: string;
};

export type ProductListItem = Product & {
  category: Category;
  brand: Brand | null;
  main_image: ProductImage | null;
};

export type ProductDetail = Product & {
  category: number;
  category_detail: Category;
  brand: number | null;
  brand_detail: Brand | null;
  images: ProductImage[];
};

export type User = {
  id: number;
  phone_number: string;
  first_name: string;
  last_name: string;
  email: string;
  is_phone_verified: boolean;
  date_joined: string;
};

export type AuthTokens = {
  access: string;
  refresh: string;
  user: User;
};

export type CartItem = {
  id: number;
  product: Product;
  quantity: number;
  subtotal?: number;
  created_at?: string;
};

export type Cart = {
  items: CartItem[];
  total_items: number;
  total_price?: number;
  subtotal?: number;
};

export type Coupon = {
  id: number;
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  max_discount_amount: number | null;
  min_order_amount: number;
  usage_limit: number | null;
  used_count: number;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type OrderItem = {
  id: number;
  product: number | Product;
  product_name: string;
  product_price: number;
  quantity: number;
  line_total: number;
};

export type Order = {
  id: number;
  user?: number | User;
  status:
    | "pending"
    | "paid"
    | "processing"
    | "shipped"
    | "delivered"
    | "cancelled";
  stock_reduced: boolean;
  coupon: number | Coupon | null;
  subtotal_amount: number;
  discount_amount: number;
  shipping_cost: number;
  total_amount: number;
  shipping_address: string;
  postal_code: string;
  recipient_name: string;
  recipient_phone: string;
  items?: OrderItem[];
  created_at: string;
  updated_at: string;
};

export type Payment = {
  id: number;
  user: number | User;
  order: number | Order;
  gateway: "zarinpal";
  amount: number;
  status: "pending" | "paid" | "failed" | "cancelled";
  authority: string | null;
  ref_id: string | null;
  card_pan: string | null;
  gateway_response: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  paid_at: string | null;
};
