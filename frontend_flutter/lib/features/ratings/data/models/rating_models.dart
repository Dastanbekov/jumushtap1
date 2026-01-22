import 'package:json_annotation/json_annotation.dart';

part 'rating_models.g.dart';

@JsonSerializable()
class RatingHistory {
  final int id;
  @JsonKey(name: 'old_rating')
  final double oldRating;
  @JsonKey(name: 'new_rating')
  final double newRating;
  final String reason;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  final Map<String, dynamic>? details;

  RatingHistory({
    required this.id,
    required this.oldRating,
    required this.newRating,
    required this.reason,
    required this.createdAt,
    this.details,
  });

  factory RatingHistory.fromJson(Map<String, dynamic> json) =>
      _$RatingHistoryFromJson(json);
  Map<String, dynamic> toJson() => _$RatingHistoryToJson(this);
}

@JsonSerializable()
class Review {
  final int id;
  final int user; // ID of the user being reviewed
  final int author; // ID of the reviewer
  final int rating;
  final String? text;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  Review({
    required this.id,
    required this.user,
    required this.author,
    required this.rating,
    this.text,
    required this.createdAt,
  });

  factory Review.fromJson(Map<String, dynamic> json) => _$ReviewFromJson(json);
  Map<String, dynamic> toJson() => _$ReviewToJson(this);
}

@JsonSerializable()
class RatingConfig {
  @JsonKey(name: 'recency_weight')
  final double recencyWeight;
  @JsonKey(name: 'verified_user_weight')
  final double verifiedUserWeight;

  RatingConfig({
    required this.recencyWeight,
    required this.verifiedUserWeight,
  });

  factory RatingConfig.fromJson(Map<String, dynamic> json) =>
      _$RatingConfigFromJson(json);
  Map<String, dynamic> toJson() => _$RatingConfigToJson(this);
}
