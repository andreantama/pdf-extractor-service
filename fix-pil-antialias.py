#!/usr/bin/env python3
"""
Fix script untuk mengatasi PIL.Image.ANTIALIAS error pada Pillow 10.0.0+
"""

import sys
import subprocess

def install_compatible_pillow():
    """Install versi Pillow yang kompatibel"""
    
    print("🔧 Fixing PIL.Image.ANTIALIAS compatibility issue...")
    print("=" * 60)
    
    try:
        import PIL
        print(f"📦 Current Pillow version: {PIL.__version__}")
    except ImportError:
        print("📦 Pillow not installed")
    
    print("\n🔄 Installing compatible Pillow version...")
    
    # Uninstall current Pillow dan install versi yang kompatibel
    commands = [
        ["pip", "uninstall", "-y", "Pillow"],
        ["pip", "install", "Pillow==10.3.0"],
        ["pip", "install", "--upgrade", "easyocr==1.7.1"]
    ]
    
    for cmd in commands:
        print(f"   Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Error: {result.stderr}")
            else:
                print(f"   ✅ Success")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n🧪 Testing PIL import...")
    test_code = """
import sys
try:
    from PIL import Image
    print("✅ PIL import successful")
    
    # Test ANTIALIAS attribute
    if hasattr(Image, 'ANTIALIAS'):
        print("✅ Image.ANTIALIAS available")
    else:
        print("⚠️  Image.ANTIALIAS not available, but LANCZOS should work")
        print("✅ Image.LANCZOS available:", hasattr(Image, 'LANCZOS'))
    
    # Test EasyOCR import
    import easyocr
    print("✅ EasyOCR import successful")
    
    print("\\n🎉 All imports working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except AttributeError as e:
    print(f"❌ Attribute error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([sys.executable, "-c", test_code], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
            
        if result.returncode == 0:
            print("\n✅ PIL.Image.ANTIALIAS fix completed successfully!")
            return True
        else:
            print("\n❌ Fix failed - please check error messages above")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing fix: {e}")
        return False

def show_fix_alternatives():
    """Show alternative fixes"""
    print("\n💡 Alternative Solutions:")
    print("=" * 30)
    
    print("\n1. Use older Pillow version:")
    print("   pip install Pillow==9.5.0")
    
    print("\n2. Update all dependencies:")
    print("   pip install --upgrade -r requirements.txt")
    
    print("\n3. Manual compatibility patch (already applied in worker_app/main.py):")
    print("""
   # Add this to your code before importing PIL-dependent libraries
   from PIL import Image
   if not hasattr(Image, 'ANTIALIAS'):
       Image.ANTIALIAS = Image.LANCZOS
   """)
    
    print("\n4. Use specific EasyOCR version:")
    print("   pip install easyocr==1.7.1")

def main():
    """Main function"""
    print("🚀 PDF Extractor - PIL.Image.ANTIALIAS Fix")
    print("=" * 50)
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not in virtual environment. Consider activating venv first:")
        print("   source venv/bin/activate")
        print("")
    
    success = install_compatible_pillow()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Restart your PDF extractor service")
        print("2. Test with: python3 test-knowledge.py")
        print("3. If issues persist, check alternative solutions below")
    
    show_fix_alternatives()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)