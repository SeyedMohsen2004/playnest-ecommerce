export type PaymentFailureReason =
  | "missing_authority"
  | "invalid_callback_status"
  | "payment_not_found"
  | "cancelled_or_failed"
  | "verification_failed"
  | "verification_unavailable"
  | "finalization_failed"
  | "order_cancelled"
  | "unknown";

type AnalyticsEventProperties = {
  add_to_cart: {
    category_slug: string;
    product_id: number;
    product_slug: string;
    quantity: number;
  };
  checkout_started: {
    item_count: number;
    shipping_zone: string;
    total: number;
  };
  coupon_applied: {
    discount: number;
    total: number;
  };
  payment_started: {
    amount: number;
  };
  purchase_completed: {
    item_count: number;
    shipping_zone: string;
    total: number;
  };
  payment_failed: {
    reason: PaymentFailureReason;
  };
};

export type AnalyticsEventName = keyof AnalyticsEventProperties;

type UmamiTracker = {
  track: <EventName extends AnalyticsEventName>(
    eventName: EventName,
    properties: Readonly<AnalyticsEventProperties[EventName]>,
  ) => void | Promise<void>;
};

declare global {
  interface Window {
    umami?: UmamiTracker;
  }
}

const trackedEventKeys = new Set<string>();
const sessionStoragePrefix = "playnest:analytics:";

export function trackEvent<EventName extends AnalyticsEventName>(
  eventName: EventName,
  properties: Readonly<AnalyticsEventProperties[EventName]>,
) {
  if (typeof window === "undefined" || typeof window.umami?.track !== "function") {
    return false;
  }

  try {
    void Promise.resolve(window.umami.track(eventName, properties)).catch(
      () => undefined,
    );
    return true;
  } catch {
    return false;
  }
}

export function trackEventOnce<EventName extends AnalyticsEventName>(
  eventKey: string,
  eventName: EventName,
  properties: Readonly<AnalyticsEventProperties[EventName]>,
) {
  if (typeof window === "undefined" || trackedEventKeys.has(eventKey)) {
    return false;
  }

  const storageKey = `${sessionStoragePrefix}${eventKey}`;

  try {
    if (window.sessionStorage.getItem(storageKey) === "1") {
      trackedEventKeys.add(eventKey);
      return false;
    }
  } catch {
    // In-memory deduplication still applies when browser storage is unavailable.
  }

  if (!trackEvent(eventName, properties)) {
    return false;
  }

  trackedEventKeys.add(eventKey);

  try {
    window.sessionStorage.setItem(storageKey, "1");
  } catch {
    // Analytics must remain non-blocking when browser storage is unavailable.
  }

  return true;
}
