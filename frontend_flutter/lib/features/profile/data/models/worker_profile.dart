import 'package:json_annotation/json_annotation.dart';

part 'worker_profile.g.dart';

@JsonSerializable()
class Skill {
  final int id;
  final String name;

  Skill({required this.id, required this.name});

  factory Skill.fromJson(Map<String, dynamic> json) => _$SkillFromJson(json);
  Map<String, dynamic> toJson() => _$SkillToJson(this);
}

@JsonSerializable()
class WorkerProfile {
  final int id;
  @JsonKey(name: 'birth_date')
  final DateTime? birthDate;
  @JsonKey(name: 'passport_series')
  final String? passportSeries;
  @JsonKey(name: 'passport_number')
  final String? passportNumber;
  @JsonKey(name: 'experience_years')
  final int experienceYears;
  final String about;
  final List<Skill> skills;
  @JsonKey(name: 'verification_status')
  final String verificationStatus;
  @JsonKey(name: 'rejection_reason')
  final String? rejectionReason;

  WorkerProfile({
    required this.id,
    this.birthDate,
    this.passportSeries,
    this.passportNumber,
    this.experienceYears = 0,
    this.about = '',
    this.skills = const [],
    this.verificationStatus = 'unverified',
    this.rejectionReason,
  });

  factory WorkerProfile.fromJson(Map<String, dynamic> json) =>
      _$WorkerProfileFromJson(json);
  Map<String, dynamic> toJson() => _$WorkerProfileToJson(this);
}
