import { PaymentClient } from "@/app/payment/[orderId]/payment-client";

export default async function PaymentPage({
  params,
}: {
  params: Promise<{ orderId: string }>;
}) {
  const { orderId } = await params;

  return <PaymentClient orderId={orderId} />;
}
