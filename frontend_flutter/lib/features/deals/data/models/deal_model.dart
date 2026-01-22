import 'package:json_annotation/json_annotation.dart';

part 'deal_model.g.dart';

@JsonSerializable()
class Deal {
  final int id;
  // Assumes Order model exists or we use ID/Map for simplicity if missing, but ideally Order object
  // For MVP, we might just store order ID or simple object. 
  // Given existing deals feature, I should check if there is an Order model used. 
  // If not, I'll use Map for order.
  final Map<String, dynamic> order; 
  final Map<String, dynamic> customer;
  final Map<String, dynamic> worker;
  
  final String status;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  
  // QR & Time Tracking
  @JsonKey(name: 'qr_token')
  final String? qrToken;
  @JsonKey(name: 'started_at')
  final DateTime? startedAt;
  @JsonKey(name: 'finished_at')
  final DateTime? finishedAt;
  
  // Confirmed
  @JsonKey(name: 'worker_confirmed')
  final bool workerConfirmed;
  @JsonKey(name: 'customer_confirmed')
  final bool customerConfirmed;

  Deal({
    required this.id,
    required this.order,
    required this.customer,
    required this.worker,
    required this.status,
    required this.createdAt,
    this.qrToken,
    this.startedAt,
    this.finishedAt,
    this.workerConfirmed = false,
    this.customerConfirmed = false,
  });

  factory Deal.fromJson(Map<String, dynamic> json) => _$DealFromJson(json);
  Map<String, dynamic> toJson() => _$DealToJson(this);
}
