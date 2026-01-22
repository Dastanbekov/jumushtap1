import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../../auth/providers/auth_provider.dart';

// Provider for verification logic (simplified for MVP)
final verificationProvider = FutureProvider.family<void, FormData>((ref, data) async {
  // TODO: implement API call to /users/me/verify/
  // final dio = ref.read(apiClientProvider);
  // await dio.post('/users/me/verify/', data: data); 
});

class VerificationScreen extends ConsumerStatefulWidget {
  const VerificationScreen({super.key});

  @override
  ConsumerState<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends ConsumerState<VerificationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _picker = ImagePicker();
  
  // Worker fields
  File? _passportFront;
  File? _passportBack;
  
  // Customer fields
  final _innController = TextEditingController();
  final _companyNameController = TextEditingController();

  Future<void> _pickImage(bool isFront) async {
    final picked = await _picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      setState(() {
        if (isFront) {
          _passportFront = File(picked.path);
        } else {
          _passportBack = File(picked.path);
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    // Assuming 'role' is in the user map. If using UserModel, adapt accordingly.
    final role = user?['role'] as String? ?? 'customer'; 

    return Scaffold(
      appBar: AppBar(title: const Text('Account Verification')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Verify your ${role.toUpperCase()} account',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 20),
              
              if (role == 'worker') ...[
                 const Text('Passport Scan (Front)'),
                 const SizedBox(height: 8),
                 _buildImagePicker(true),
                 const SizedBox(height: 16),
                 const Text('Passport Scan (Back)'),
                 const SizedBox(height: 8),
                 _buildImagePicker(false),
              ] else ...[
                TextFormField(
                  controller: _companyNameController,
                  decoration: const InputDecoration(labelText: 'Company Name'),
                  validator: (v) => v!.isEmpty ? 'Required' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _innController,
                  decoration: const InputDecoration(labelText: 'INN (Tax ID)'),
                  validator: (v) => v!.isEmpty ? 'Required' : null,
                ),
              ],
              
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatorButton(
                  onPressed: () {
                    if (_formKey.currentState!.validate()) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Submitting for verification...')),
                      );
                      // Trigger provider logic here
                    }
                  },
                  child: const Text('Submit for Verification'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildImagePicker(bool isFront) {
    final file = isFront ? _passportFront : _passportBack;
    return InkWell(
      onTap: () => _pickImage(isFront),
      child: Container(
        height: 150,
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.grey[200],
          border: Border.all(color: Colors.grey),
          borderRadius: BorderRadius.circular(8),
        ),
        child: file != null
            ? Image.file(file, fit: BoxFit.cover)
            : const Center(child: Icon(Icons.add_a_photo, size: 40, color: Colors.grey)),
      ),
    );
  }
}
