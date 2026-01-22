import 'package:json_annotation/json_annotation.dart';
import '../../profile/data/models/worker_profile.dart';
import '../../profile/data/models/customer_profile.dart';

part 'user_model.g.dart';

@JsonSerializable()
class User {
  final int id;
  final String username;
  final String email;
  final String role;
  
  @JsonKey(name: 'first_name')
  final String? firstName;
  @JsonKey(name: 'last_name')
  final String? lastName;

  // Rating & Verification
  final double rating;
  @JsonKey(name: 'rating_count')
  final int ratingCount;
  @JsonKey(name: 'is_verified')
  final bool isVerified;
  
  // Profiles
  @JsonKey(name: 'worker_profile')
  final WorkerProfile? workerProfile;
  @JsonKey(name: 'customer_profile')
  final CustomerProfile? customerProfile;

  User({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    this.firstName,
    this.lastName,
    this.rating = 0.0,
    this.ratingCount = 0,
    this.isVerified = false,
    this.workerProfile,
    this.customerProfile,
  });

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);
}
