import 'package:json_annotation/json_annotation.dart';

part 'customer_profile.g.dart';

@JsonSerializable()
class CustomerProfile {
  final int id;
  @JsonKey(name: 'company_name')
  final String companyName;
  final String inn;
  @JsonKey(name: 'legal_address')
  final String legalAddress;
  @JsonKey(name: 'contact_person')
  final String contactPerson;
  final String website;
  @JsonKey(name: 'verification_status')
  final String verificationStatus;
  @JsonKey(name: 'rejection_reason')
  final String? rejectionReason;

  CustomerProfile({
    required this.id,
    this.companyName = '',
    this.inn = '',
    this.legalAddress = '',
    this.contactPerson = '',
    this.website = '',
    this.verificationStatus = 'unverified',
    this.rejectionReason,
  });

  factory CustomerProfile.fromJson(Map<String, dynamic> json) =>
      _$CustomerProfileFromJson(json);
  Map<String, dynamic> toJson() => _$CustomerProfileToJson(this);
}
