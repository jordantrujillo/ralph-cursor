import { test } from 'node:test';
import assert from 'node:assert';
import { spawn } from 'child_process';
import { mkdtemp, rm, readFile, access, constants } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';

const CLI_PATH = join(process.cwd(), 'bin', 'ralph.js');

async function runCLI(args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn('node', [CLI_PATH, ...args], {
      cwd,
      stdio: 'pipe',
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('exit', (code) => {
      resolve({ code, stdout, stderr });
    });

    child.on('error', reject);
  });
}

test('ralph init creates scripts/ralph/ directory and files', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    const result = await runCLI(['init'], testDir);
    assert.strictEqual(result.code, 0, `Expected exit code 0, got ${result.code}. stderr: ${result.stderr}`);

    // Check that required files were created
    const requiredFiles = [
      'scripts/ralph/ralph.py',
      'scripts/ralph/prompt.md',
      'scripts/ralph/prd.yml.example',
      'scripts/ralph/cursor/prompt.cursor.md',
      'scripts/ralph/cursor/prompt.convert-to-prd-yml.md',
      'scripts/ralph/cursor/prompt.generate-prd.md',
      'scripts/ralph/cursor/convert-to-prd-yml.sh',
    ];

    for (const file of requiredFiles) {
      const filePath = join(testDir, file);
      try {
        await access(filePath, constants.F_OK);
      } catch (err) {
        assert.fail(`File ${file} was not created`);
      }
    }

    // Check that ralph.py is executable
    try {
      await access(join(testDir, 'scripts/ralph/ralph.py'), constants.X_OK);
    } catch (err) {
      assert.fail('ralph.py is not executable');
    }

    // Check that convert-to-prd-yml.sh is executable
    try {
      await access(join(testDir, 'scripts/ralph/cursor/convert-to-prd-yml.sh'), constants.X_OK);
    } catch (err) {
      assert.fail('convert-to-prd-yml.sh is not executable');
    }

    assert(result.stdout.includes('Created') || result.stdout.includes('file'), 'Should show files were created');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph init does not overwrite existing files by default', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    // First init
    await runCLI(['init'], testDir);

    // Read original content
    const originalContent = await readFile(join(testDir, 'scripts/ralph/prompt.md'), 'utf-8');

    // Modify the file
    const modifiedContent = originalContent + '\n# Modified';
    await import('fs/promises').then(fs => fs.writeFile(join(testDir, 'scripts/ralph/prompt.md'), modifiedContent));

    // Run init again
    const result = await runCLI(['init'], testDir);
    assert.strictEqual(result.code, 0);

    // Check that file was not overwritten
    const currentContent = await readFile(join(testDir, 'scripts/ralph/prompt.md'), 'utf-8');
    assert.strictEqual(currentContent, modifiedContent, 'File should not be overwritten');
    assert(result.stdout.includes('Skipped'), 'Should show files were skipped');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph init --force overwrites existing files', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    // First init
    await runCLI(['init'], testDir);

    // Modify the file
    const modifiedContent = '# Modified';
    await import('fs/promises').then(fs => fs.writeFile(join(testDir, 'scripts/ralph/prompt.md'), modifiedContent));

    // Run init with --force
    const result = await runCLI(['init', '--force'], testDir);
    assert.strictEqual(result.code, 0);

    // Check that file was overwritten (should have original content, not modified)
    const currentContent = await readFile(join(testDir, 'scripts/ralph/prompt.md'), 'utf-8');
    assert.notStrictEqual(currentContent, modifiedContent, 'File should be overwritten');
    assert(currentContent.length > modifiedContent.length, 'File should have original content');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph run invokes repo-local runner', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    // Initialize
    await runCLI(['init'], testDir);

    // Create stub runner that just prints a message
    const stubRunner = `#!/usr/bin/env python3
import sys
print("STUB_RUNNER_CALLED")
print(f"ITERATIONS: {sys.argv[1] if len(sys.argv) > 1 else '10'}")
sys.exit(0)
`;
    await import('fs/promises').then(fs => fs.writeFile(join(testDir, 'scripts/ralph/ralph.py'), stubRunner));
    await import('fs/promises').then(fs => fs.chmod(join(testDir, 'scripts/ralph/ralph.py'), 0o755));

    // Create stub binaries
    const binDir = join(testDir, 'bin');
    await import('fs/promises').then(fs => fs.mkdir(binDir, { recursive: true }));


    // Run with modified PATH
    const env = { ...process.env, PATH: `${binDir}:${process.env.PATH}` };
    const result = await new Promise((resolve, reject) => {
      const child = spawn('node', [CLI_PATH, 'run', '--iterations', '5'], {
        cwd: testDir,
        env,
        stdio: 'pipe',
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('exit', (code) => {
        resolve({ code, stdout, stderr });
      });

      child.on('error', reject);
    });

    assert(result.stdout.includes('STUB_RUNNER_CALLED'), 'Runner should be invoked');
    assert(result.stdout.includes('ITERATIONS: 5'), 'Iterations should be passed');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph run executes ralph.py', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    // Initialize
    await runCLI(['init'], testDir);

    // Create stub runner
    const stubRunner = `#!/usr/bin/env python3
import sys
print("STUB_RUNNER_CALLED")
print(f"ITERATIONS: {sys.argv[1] if len(sys.argv) > 1 else '10'}")
sys.exit(0)
`;
    await import('fs/promises').then(fs => fs.writeFile(join(testDir, 'scripts/ralph/ralph.py'), stubRunner));
    await import('fs/promises').then(fs => fs.chmod(join(testDir, 'scripts/ralph/ralph.py'), 0o755));

    // Create stub cursor binary
    const binDir = join(testDir, 'bin');
    await import('fs/promises').then(fs => fs.mkdir(binDir, { recursive: true }));

    const stubCursor = `#!/bin/bash
echo "stub cursor"
exit 0
`;
    await import('fs/promises').then(fs => fs.writeFile(join(binDir, 'cursor'), stubCursor));
    await import('fs/promises').then(fs => fs.chmod(join(binDir, 'cursor'), 0o755));

    // Run with cursor worker
    const env = { ...process.env, PATH: `${binDir}:${process.env.PATH}` };
    const result = await new Promise((resolve, reject) => {
      const child = spawn('node', [CLI_PATH, 'run'], {
        cwd: testDir,
        env,
        stdio: 'pipe',
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('exit', (code) => {
        resolve({ code, stdout, stderr });
      });

      child.on('error', reject);
    });

    assert(result.stdout.includes('STUB_RUNNER_CALLED'), 'Runner should be invoked');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph run fails if not initialized', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    const result = await runCLI(['run'], testDir);
    assert.notStrictEqual(result.code, 0, 'Should exit with error code');
    assert(result.stderr.includes('not initialized') || result.stdout.includes('not initialized'), 'Should indicate Ralph is not initialized');
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});

test('ralph init installs cursor files', async () => {
  const testDir = await mkdtemp(join(tmpdir(), 'ralph-test-'));
  try {
    const result = await runCLI(['init'], testDir);
    assert.strictEqual(result.code, 0);

    // Check cursor files exist
    await access(join(testDir, 'scripts/ralph/cursor/prompt.cursor.md'), constants.F_OK);
    await access(join(testDir, 'scripts/ralph/cursor/convert-to-prd-yml.sh'), constants.F_OK);

    // Check common files exist
    await access(join(testDir, 'scripts/ralph/ralph.py'), constants.F_OK);
    await access(join(testDir, 'scripts/ralph/prd.yml.example'), constants.F_OK);
  } finally {
    await rm(testDir, { recursive: true, force: true });
  }
});
