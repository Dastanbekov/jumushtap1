import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class QrScanScreen extends StatefulWidget {
  final Function(String) onScan;

  const QrScanScreen({super.key, required this.onScan});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
  // MobileScannerController controller = MobileScannerController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan QR Code')),
      body: MobileScanner(
        onDetect: (capture) {
          final List<Barcode> barcodes = capture.barcodes;
           for (final barcode in barcodes) {
            if (barcode.rawValue != null) {
               widget.onScan(barcode.rawValue!);
               Navigator.pop(context); // Close scanner after success
               break; 
            }
          }
        },
      ),
    );
  }
}
